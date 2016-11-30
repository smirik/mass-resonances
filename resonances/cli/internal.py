import logging
import os
import re
from logging.handlers import RotatingFileHandler
from os.path import join as opjoin

import click
from resonances.shortcuts import is_s3

from resonances.entities.resonance import BodyNumberEnum
from resonances.settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
INTEGRATOR_DIR = CONFIG['integrator']['dir']


def _unite_decorators(*decorators):
    def deco(decorated_function):
        for dec in reversed(decorators):
            decorated_function = dec(decorated_function)
        return decorated_function

    return deco


def _try_to_int(val: str, option: click.Option):
    try:
        int(val)
    except ValueError:
        raise click.BadOptionUsage(option, 'Invalid integers.')


def validate_or_set_body_count(ctx: click.Context, option: click.Option, value: str):
    ints = ctx.params.get('integers', None)
    if type(ints) == str:
        ints = ints.split()
    integers_count = len(ints) if ints else None
    if integers_count:
        if not value:
            return integers_count
        if int(value) != integers_count:
            raise click.BadOptionUsage(option, '--body-count must be equal number of integers')
        return value
    return value or 3


def validate_integer_expression(ctx: click.Context, option: click.Option, value: str):
    if not value:
        return value
    vals = value.split()

    error_message = 'Invalid integers. Check --help'
    try:
        BodyNumberEnum(len(vals))
    except ValueError:
        raise click.BadOptionUsage(option, error_message)

    bool_ops = ['<', '>', '<=', '>=']
    for i, val in enumerate(vals):
        if val == '*':
            continue

        res = re.search('([0-9])', val)
        if res:
            number_part_start = res.start()
            symbol = val[:number_part_start]
            _try_to_int(val[number_part_start:], option)
            if not symbol or symbol == '-':
                vals[i] = '==%s' % val
            elif symbol not in bool_ops:
                raise click.BadOptionUsage(option, 'Invalid operators before integers.')
        else:
            raise click.BadOptionUsage(option, error_message)

    return vals


def report_interval_options():
    return _unite_decorators(
        click.option('--limit', default=100, type=int, help='Example: 100'),
        click.option('--offset', default=0, type=int, help='Example: 100'))


def asteroid_interval_options(default_start=1, default_stop=101):
    return _unite_decorators(
        click.option('--start', default=default_start, type=int,
                     help='Start asteroid number. Counting from 1.'),
        click.option('--stop', default=default_stop, type=int,
                     help='Stop asteroid number. Excepts last. Means, that '
                          'asteroid with number, that equals this parameter,'
                          ' will not be integrated.'))


class Path(click.Path):
    def convert(self, value, param, ctx):
        if is_s3(value):
            rv = value
            return rv
        return super(Path, self).convert(value, param, ctx)


def aei_path_options():
    return _unite_decorators(
        click.option('--aei-paths', '-p', multiple=True,
                     default=(opjoin(PROJECT_DIR, INTEGRATOR_DIR),),
                     type=Path(exists=True, resolve_path=True),
                     help='Path to aei files. It can be folder or tar.gz archive.'
                          ' You can point several paths. Example: -p /mnt/aei/ -p /tmp/aei'),
        click.option('--recursive', '-r', type=bool, is_flag=True,
                     help='Indicates about recursive search aei file in pointed paths.'),
    )


def asteroid_time_intervals_options():
    prefix = 'This parameter will be passed to param.in file for integrator Mercury6 as'
    return _unite_decorators(
        asteroid_interval_options(),
        click.option('--from-day', default=2451000.5, help='%s start time pointed in days.' %
                                                           prefix),
        click.option('--to-day', default=2501000.5,
                     help='%s stop time pointed in days.' % prefix))


def build_logging(loglevel: str, logfile: str, message_format: str, time_format: str):
    if logfile:
        logpath = opjoin(PROJECT_DIR, 'logs')
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        path = opjoin(logpath, logfile)
        loghandler = RotatingFileHandler(path, mode='a', maxBytes=10 * 1024 * 1024,
                                         backupCount=10, encoding=None, delay=0)
        loghandler.setFormatter(logging.Formatter(message_format, time_format))
        loghandler.setLevel(loglevel)

        logger = logging.getLogger()
        logger.setLevel(loglevel)
        logger.addHandler(loghandler)
    else:
        logging.basicConfig(
            format=message_format,
            datefmt=time_format,
            level=loglevel,
        )


def validate_ints(ctx: click.Context, option: click.Option, value: str):
    res = [int(x) for x in value.split()]
    if not (2 <= len(res) <= 3):
        error_message = 'Incorrect integers. Correct examples \'5 -1 -1\' or \'1 -1\''
        raise click.BadOptionUsage(option.name, error_message)
    return res


def validate_planets(ctx: click.Context, option: click.Option, value: str):
    if len(value) == len(ctx.params['integers']) - 1:
        return value
    raise click.BadParameter('Incorrect number of planets for pointed integers.')

