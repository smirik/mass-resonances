import logging

import click

from commands import calc as _calc
from commands import find as _find
from commands import plot as _plot
from commands import package as _package
from commands import remove_export_directory
from storage import extract as _extract

LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


@click.group()
@click.option('--loglevel', default='DEBUG', help='default: DEBUG',
              type=click.Choice(LEVELS))
@click.pass_context
def cli(loglevel: str = 'DEBUG'):
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, loglevel)
    )


@cli.command()
@click.option('--start', default=1)
def calc(start: int):
    _calc(start)


@cli.command()
@click.option('--start', default=1)
@click.option('--stop', default=101)
def find(start: int, stop: int):
    _find(start, stop)


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

