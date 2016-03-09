import logging
import os
import click
from catalog import save_resonances
from logging.handlers import RotatingFileHandler
from commands import calc as _calc
from commands import find as _find
from commands import plot as _plot
from commands import package as _package
from commands import remove_export_directory
from commands.show_broken_bodies import show_broken_bodies
from integrator import set_time_interval
from storage import extract as _extract
from settings import Config
from os.path import join as opjoin

LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
RESONANCE_TABLE_FILE = CONFIG['resonance_table']['file']
RESONANCE_FILEPATH = opjoin(PROJECT_DIR, 'axis', RESONANCE_TABLE_FILE)
STEP = CONFIG['integrator']['number_of_bodies']


def _unite_decorators(*decorators):
    def deco(decorated_function):
        for dec in reversed(decorators):
            decorated_function = dec(decorated_function)
        return decorated_function

    return deco


def _asteroid_interval_options():
    return _unite_decorators(
        click.option('--start', default=1, type=int,
                     help='Start asteroid number. Counting from 1.'),
        click.option('--stop', default=101, type=int,
                     help='Stop asteroid number. Excepts last. Means, that '
                          'asteroid with number, that equals this parameter,'
                          ' will not be integrated.'))


def _asteroid_time_intervals_options():
    prefix = 'This parameter will be passed to param.in file for integrator Mercury6 as'
    return _unite_decorators(
        _asteroid_interval_options(),
        click.option('--from-day', default=2451000.5, help='%s start time pointed in days.' %
                                                           prefix),
        click.option('--to-day', default=2501000.5,
                     help='%s stop time pointed in days.' % prefix))


def _build_logging(loglevel: str, logfile: str, message_format: str, time_format: str):
    if logfile:
        logpath = opjoin(PROJECT_DIR, 'logs')
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        path = opjoin(logpath, logfile)
        loghandler = RotatingFileHandler(path, mode='a', maxBytes=10*1024*1024,
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


@click.group()
@click.option('--loglevel', default='DEBUG', help='default: DEBUG',
              type=click.Choice(LEVELS))
@click.option('--logfile', default=None, help='default: None',
              type=str)
def cli(loglevel: str = 'DEBUG', logfile: str = None):
    _build_logging(getattr(logging, loglevel), logfile, '%(asctime)s %(levelname)s %(message)s',
                   '%Y-%m-%d %H:%M:%S')


@cli.command(help='Launch integrator Mercury6 for computing orbital elements of asteroids and'
                  ' planets, that will be stored in aei files.')
@_asteroid_time_intervals_options()
def calc(start: int, stop: int, from_day: float, to_day: float):
    set_time_interval(from_day, to_day)
    _calc(start, stop, STEP)


FIND_HELP_PREFIX = 'If true, the application will'


@cli.command()
@_asteroid_interval_options()
def load_resonances(start: int, stop: int):
    for i in range(start, stop, STEP):
        end = i + STEP if i + STEP < stop else stop
        save_resonances(RESONANCE_FILEPATH, i, end)


@cli.command(
    help='Computes resonant phases, find in them circulations and saves to librations.'
         ' Parameters --from-day and --to-day are use only --recalc option is true.')
@_asteroid_time_intervals_options()
@click.option('--reload-resonances', default=False, type=bool,
              help='%s load integers, satisfying D\'Alamebrt rule, from %s.' %
                   (FIND_HELP_PREFIX, RESONANCE_FILEPATH))
@click.option('--recalc', default=False, type=bool, help='%s invoke calc method before' %
                                                         FIND_HELP_PREFIX)
@click.option('--is-current', default=False, type=bool,
              help='%s librations only from database, it won\'t compute them from phases' %
                   FIND_HELP_PREFIX)
@click.option('--migrate-phases', default=False, type=bool,
              help='will loads phases to postgres from redis')
def find(start: int, stop: int, from_day: float, to_day: float, reload_resonances: bool,
         recalc: bool, is_current: bool, migrate_phases: bool):
    if recalc:
        set_time_interval(from_day, to_day)
        _calc(start, stop, STEP)
    for i in range(start, stop, STEP):
        end = i + STEP if i + STEP < stop else stop
        if reload_resonances:
            save_resonances(RESONANCE_FILEPATH, i, end)
        _find(i, end, is_current, migrate_phases)


@cli.command(help='Build graphics for asteroids in pointed interval, that have libration.'
                  ' Libration can be created by command \'find\'.')
@_asteroid_interval_options()
@click.option('--from-db', default=False, type=bool,
              help='If true, applicatioin will loads resonant phases from database instead redis.')
def plot(start: int, stop: int, from_db: bool):
    _plot(start, stop, from_db)


@cli.command()
@_asteroid_interval_options()
def clean(start: int, stop: int):
    remove_export_directory(start, stop)


@cli.command()
@click.option('--start', default=1)
@click.option('--copy-aei', default=False, type=bool)
def extract(start: int, copy_aei: bool):
    _extract(start, do_copy_aei=copy_aei)


@cli.command()
@_asteroid_interval_options()
@click.option('--res', default=False, type=bool)
@click.option('--aei', default=False, type=bool)
@click.option('--compress', default=False, type=bool)
def package(start: int, stop: int, res: bool, aei: bool, compress: bool):
    _package(start, stop, res, aei, compress)


@cli.command()
def broken_bodies():
    show_broken_bodies()
