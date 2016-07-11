import click
import logging
from logging.handlers import RotatingFileHandler
from os.path import join as opjoin
from settings import Config
import os
from shortcuts import is_s3

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
INTEGRATOR_DIR = CONFIG['integrator']['dir']


def _unite_decorators(*decorators):
    def deco(decorated_function):
        for dec in reversed(decorators):
            decorated_function = dec(decorated_function)
        return decorated_function

    return deco


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

