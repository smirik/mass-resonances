import logging
import os
import click
from catalog import save_resonances
from commands import calc as _calc
from commands import find as _find
from commands import plot as _plot
from commands import package as _package
from commands import remove_export_directory
from integrator import set_time_interval
from storage import extract as _extract
from settings import Config
from os.path import join as opjoin

LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
RESONANCE_TABLE_FILE = CONFIG['resonance_table']['file']
RESONANCE_FILEPATH = opjoin(PROJECT_DIR, 'axis', RESONANCE_TABLE_FILE)
STEP = 100


def _unite_decorators(*decorators):
    def deco(decorated_function):
        for dec in reversed(decorators):
            decorated_function = dec(decorated_function)
        return decorated_function
    return deco


def _asteroid_interval_options():
    decs = (
        click.option('--start', default=1),
        click.option('--stop', default=101)
    )
    return _unite_decorators(*decs)


def _asteroid_time_intervals_options():
    decs = (
        _asteroid_interval_options(),
        click.option('--from-day', default=2451000.5),
        click.option('--to-day', default=2501000.5)
    )
    return _unite_decorators(*decs)


@click.group()
@click.option('--loglevel', default='DEBUG', help='default: DEBUG',
              type=click.Choice(LEVELS))
@click.option('--logfile', default=None, help='default: None',
              type=str)
def cli(loglevel: str = 'DEBUG', logfile: str = None):
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, loglevel),
        filename=os.path.join(PROJECT_DIR, logfile) if logfile else None,
        filemode='w' if logfile else None
    )


@cli.command()
@_asteroid_time_intervals_options()
def calc(start: int, stop: int, from_day: float, to_day: float):
    set_time_interval(from_day, to_day)
    for i in range(start, stop, STEP):
        end = i + STEP if i + STEP < stop else stop
        _calc(i, end)


@cli.command()
@_asteroid_time_intervals_options()
@click.option('--reload-resonances', default=False, type=bool)
@click.option('--recalc', default=False, type=bool)
@click.option('--is-current', default=False, type=bool)
def find(start: int, stop: int, from_day: float, to_day: float, reload_resonances: bool,
         recalc: bool, is_current: bool):
    set_time_interval(from_day, to_day)
    for i in range(start, stop, STEP):
        end = i + STEP if i + STEP < stop else stop
        if recalc:
            _calc(i, end)
        if reload_resonances:
            save_resonances(RESONANCE_FILEPATH, i, end)
        _find(i, end, is_current)


@cli.command(help='Build graphics for asteroids in pointed interval, that have libration.'
                  ' Libration can be created by command \'find\'.')
@_asteroid_interval_options()
@click.option('--force', default=False, type=bool)
def plot(start: int, stop: int, force: bool):
    _plot(start, stop, force)


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
