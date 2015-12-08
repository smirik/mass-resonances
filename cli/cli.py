import logging

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


@click.group()
@click.option('--loglevel', default='DEBUG', help='default: DEBUG',
              type=click.Choice(LEVELS))
def cli(loglevel: str = 'DEBUG'):
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, loglevel)
    )


@cli.command()
@click.option('--start', default=1)
@click.option('--stop', default=101)
@click.option('--from-day', default=2451000.5)
@click.option('--to-day', default=2501000.5)
def calc(start: int, stop: int, from_day: float, to_day: float):
    set_time_interval(from_day, to_day)
    for i in range(start, stop, 100):
        _calc(i)


@cli.command()
@click.option('--start', default=1)
@click.option('--stop', default=101)
@click.option('--reload-resonances', default=False)
@click.option('--from-day', default=2451000.5)
@click.option('--to-day', default=2501000.5)
def find(start: int, stop: int, reload_resonances: bool, from_day: float, to_day: float):
    set_time_interval(from_day, to_day)
    for i in range(start, stop, 100):
        end = start + 100 if start + 100 < stop else stop
        if reload_resonances:
            save_resonances(RESONANCE_FILEPATH, start, end)
        _find(i, end)


@cli.command()
@click.option('--start', default=1)
@click.option('--stop', default=101)
def plot(start: int, stop: int):
    _plot(start, stop)


@cli.command()
@click.option('--start', default=1)
@click.option('--stop', default=101)
def clean(start: int, stop: int):
    remove_export_directory(start, stop)


@cli.command()
@click.option('--start', default=1)
@click.option('--copy-aei', default=False, type=bool)
def extract(start: int, copy_aei: bool):
    _extract(start, do_copy_aei=copy_aei)


@cli.command()
@click.option('--start', default=1)
@click.option('--stop', default=101)
@click.option('--res', default=False, type=bool)
@click.option('--aei', default=False, type=bool)
@click.option('--compress', default=False, type=bool)
def package(start: int, stop: int, res: bool, aei: bool, compress: bool):
    _package(start, stop, res, aei, compress)

