import logging
import os
from os.path import join as opjoin
from typing import Tuple, List, TypeVar

import click

from resonances.settings import Config
from .internal import Path
from .internal import aei_path_options
from .internal import asteroid_interval_options
from .internal import asteroid_time_intervals_options
from .internal import build_logging, validate_ints, validate_planets, validate_integer_expression, \
    validate_or_set_body_count
from .internal import report_interval_options

LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
PHASE_STORAGE = ['REDIS', 'DB', 'FILE']
PLANETS = ['EARTHMOO', 'JUPITER', 'MARS', 'MERCURY', 'NEPTUNE', 'PLUTO', 'SATURN', 'URANUS',
           'VENUS']

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
RESONANCE_TABLE_FILE = CONFIG['resonance_table']['file']
RESONANCE_FILEPATH = opjoin(PROJECT_DIR, 'axis', RESONANCE_TABLE_FILE)
STEP = CONFIG['integrator']['number_of_bodies']
INTEGRATOR_DIR = CONFIG['integrator']['dir']

BodyCountType = TypeVar('T', str, int)


@click.group()
@click.option('--loglevel', default='DEBUG', help='default: DEBUG',
              type=click.Choice(LEVELS))
@click.option('--logfile', default=None, help='default: None',
              type=str)
def cli(loglevel: str = 'DEBUG', logfile: str = None):
    build_logging(getattr(logging, loglevel), logfile, '%(asctime)s %(levelname)s %(message)s',
                  '%Y-%m-%d %H:%M:%S')


@cli.command(help='Launch integrator Mercury6 for computing orbital elements of asteroids and'
                  ' planets, that will be stored in aei files.')
@asteroid_time_intervals_options()
@click.option('--aei-path', '-p', multiple=False, default=opjoin(PROJECT_DIR, INTEGRATOR_DIR),
              type=Path(resolve_path=True),
              help='Path where will be stored aei files. It can be tar.gz archive.')
def calc(start: int, stop: int, from_day: float, to_day: float, aei_path: str):
    from resonances.commands import calc as _calc
    _calc(start, stop, STEP, from_day, to_day, aei_path)


FIND_HELP_PREFIX = 'If true, the application will'


@cli.command(
    help='Loads integers, satisfying D\'Alambert rule, from %s and build potentially' %
         RESONANCE_FILEPATH + 'resonances, that related to asteroid from catalog by' +
         ' comparing axis from this file and catalog', name='load-resonances')
@asteroid_interval_options()
@click.option('--file', default=RESONANCE_FILEPATH, type=str,
              help='Name of file in axis directory with resonances default: %s' %
                   RESONANCE_FILEPATH)
@click.option('--axis-swing', type=float,
              help='Axis swing determines swing between semi major axis of asteroid from astdys '
                   'catalog and resonance table.')
@click.argument('planets', type=click.Choice(PLANETS), nargs=-1)
def load_resonances(start: int, stop: int, file: str, axis_swing: float,
                    planets: Tuple[str]):
    assert axis_swing > 0.
    from resonances.commands import load_resonances as _load_resonances
    if not os.path.isabs(file):
        file = os.path.normpath(opjoin(os.getcwd(), file))
    if file == RESONANCE_FILEPATH:
        logging.info('%s will be used as source of integers' % file)
    for i in range(start, stop, STEP):
        end = i + STEP if i + STEP < stop else stop
        _load_resonances(file, i, end, planets, axis_swing)


@cli.command(
    help='Computes resonant phases, find in them circulations and saves to librations.'
         ' Parameters --from-day and --to-day are use only --recalc option is true.'
         ' Example: find --start=1 --stop=101 --phase-storage=FILE JUPITER MARS.'
         ' If you point --start=-1 --stop=-1 -p path/to/tar, application will load'
         ' data every asteroid from archive and work with it.')
@asteroid_time_intervals_options()
@click.option('--reload-resonances', default=False, type=bool,
              help='%s load integers, satisfying D\'Alamebrt rule, from %s.' %
                   (FIND_HELP_PREFIX, RESONANCE_FILEPATH))
@click.option('--recalc', default=False, type=bool, help='%s invoke calc method before' %
                                                         FIND_HELP_PREFIX)
@click.option('--is-current', default=False, type=bool,
              help='%s librations only from database, it won\'t compute them from phases' %
                   FIND_HELP_PREFIX)
@click.option('--phase-storage', '-s', default='FILE', type=click.Choice(PHASE_STORAGE),
              help='will save phases to redis or postgres or file')
@aei_path_options()
@click.option('--clear', '-c', type=bool, is_flag=True,
              help='Will clear resonance phases after search librations.')
@click.option('--clear-s3', type=bool, is_flag=True,
              help='Will clear downloaded s3 files after search librations.')
@click.option('--verbose', '-v', type=bool, is_flag=True, help='Shows progress bar.')
@click.argument('planets', type=click.Choice(PLANETS), nargs=-1)
def find(start: int, stop: int, from_day: float, to_day: float, reload_resonances: bool,
         recalc: bool, is_current: bool, phase_storage: str, aei_paths: Tuple[str, ...],
         recursive: bool, clear: bool, clear_s3: bool, planets: Tuple[str], verbose: bool):
    from resonances.commands import load_resonances as _load_resonances
    from resonances.datamining import PhaseStorage
    from resonances.commands import calc as _calc
    from resonances.commands import LibrationFinder

    finder = LibrationFinder(planets, recursive, clear, clear_s3, is_current,
                             PhaseStorage(PHASE_STORAGE.index(phase_storage)), verbose)
    if start == stop == -1 and aei_paths:
        finder.find_by_file(aei_paths)

    if recalc:
        _calc(start, stop, STEP, from_day, to_day)
    for i in range(start, stop, STEP):
        end = i + STEP if i + STEP < stop else stop
        if reload_resonances:
            _load_resonances(RESONANCE_FILEPATH, i, end, planets)
        finder.find(i, end, aei_paths)


@cli.command(help='Build graphics for asteroids in pointed interval, that have libration.'
                  ' Libration can be created by command \'find\'.')
@asteroid_interval_options()
@click.option('--phase-storage', default='FILE', type=click.Choice(PHASE_STORAGE),
              help='will load phases for plotting from redis or postgres or file')
@click.option('--only-librations', default=False, type=bool,
              help='flag indicates about plotting only for resonances, that librates')
@click.option('--output', '-o', default=os.getcwd(), type=Path(resolve_path=True),
              help='Directory or tar, where will be plots. By default is current directory.')
@click.option('--integers', '-i', default=None, type=str, callback=validate_integer_expression,
              help='Integers are pointing by three values separated by space. Example: \'5 -1 -1\'')
@click.option('--build-phase', '-b', default=False, type=bool, is_flag=True,
              help='It will build phases')
@aei_path_options()
@click.argument('planets', type=click.Choice(PLANETS), nargs=-1)
def plot(start: int, stop: int, phase_storage: str, only_librations: bool,
         integers: List[str], aei_paths: Tuple[str, ...], recursive: bool,
         planets: Tuple[str], output: str, build_phase: bool):
    from resonances.datamining import PhaseStorage
    from resonances.commands import plot as _plot
    _plot(start, stop, PhaseStorage(PHASE_STORAGE.index(phase_storage)),
          only_librations, integers, aei_paths, recursive, planets, output, build_phase)


@cli.command(name='clear-phases',
             help='Clears phases from database and Redis, which related to '
                  'pointed asteroids.')
@asteroid_interval_options()
@click.argument('planets', type=click.Choice(PLANETS), nargs=-1)
def clear_phases(start: int, stop: int, planets: Tuple[str]):
    from resonances.commands import clear_phases as _clear_phases
    _clear_phases(start, stop, planets)


@cli.command(help='Shows names of asteroid, that has got incorrect data in aei files.',
             name='broken-bodies')
def broken_bodies():
    from resonances.commands import show_broken_bodies
    show_broken_bodies()


@cli.command(help='Shows librations. Below options are need for filtering.')
@asteroid_interval_options(None, None)
@click.option('--first-planet', default=None, type=str, help='Example: JUPITER')
@click.option('--second-planet', default=None, type=str, help='Example: SATURN')
@click.option('--pure', default=None, type=bool, help='Example: 0')
@click.option('--apocentric', default=None, type=bool, help='Example: 0')
@click.option('--axis-interval', nargs=2, default=None, type=float,
              help='Interval is pointing by two values separated by space. Example: 0.0 180.0')
@click.option('--integers', '-i', default=None, type=str, callback=validate_integer_expression,
              help='Integers are pointing by three values separated by space. Example: \'5 -1 -1\'')
@click.option('--csv', is_flag=True)
@report_interval_options()
@click.option('--body-count', default=None, callback=validate_or_set_body_count,
              type=click.Choice(['2', '3']),
              help='Example: 2. 2 means two body resonance, 3 means three body resonance,')
def librations(start: int, stop: int, first_planet: str, second_planet: str, pure: bool,
               apocentric: bool, axis_interval: Tuple[float], integers: List[str], limit: int,
               offset: int, body_count: str, csv: bool):
    body_count = int(body_count)
    if integers and body_count != len(integers):
        raise click.BadParameter('--body-count must be equal number of --integers')
    assert not (body_count == 2 and second_planet is not None)
    from resonances.commands import AsteroidCondition
    from resonances.commands import show_librations as _show_librations
    from resonances.commands import dump_librations as _dump_librations
    from resonances.commands import PlanetCondition, AxisInterval
    kwargs = {}
    if start and stop:
        kwargs['asteroid_condition'] = AsteroidCondition(start, stop)
    kwargs['planet_condtion'] = PlanetCondition(first_planet, second_planet)
    kwargs['is_pure'] = pure
    kwargs['is_apocentric'] = apocentric
    kwargs['offset'] = offset
    kwargs['limit'] = limit
    if axis_interval:
        kwargs['axis_interval'] = AxisInterval(*axis_interval)
    if csv:
        _dump_librations(body_count=body_count, integers=integers, **kwargs)
    else:
        _show_librations(body_count=body_count, integers=integers, **kwargs)


@cli.command(help='Shows integers from resonance table. Below options are need for filtering.')
@asteroid_interval_options(None, None)
@click.option('--first-planet', default=None, type=str, help='Example: JUPITER')
@click.option('--second-planet', default=None, type=str, help='Example: SATURN')
@click.option('--body-count', default=None, type=click.Choice(['2', '3']),
              callback=validate_or_set_body_count,
              help='Example: 2. 2 means two body resonance, 3 means three body resonance,')
@report_interval_options()
@click.option('--integers', '-i', type=str, callback=validate_integer_expression, default=None,
              help='Examples: \'>1 1\', \'>=3 <5\', \'1 -1 *\'')
def resonances(start: int, stop: int, first_planet: str, second_planet: str,
               body_count: BodyCountType, limit, offset, integers: List[str]):
    from resonances.commands import AsteroidCondition
    from resonances.commands import show_resonance_table as _show_resonance_table
    from resonances.commands import PlanetCondition

    assert not (body_count == 2 and second_planet is not None)
    kwargs = {
        'body_count': int(body_count),
        'offset': offset,
        'limit': limit,
        'planet_condtion': PlanetCondition(first_planet, second_planet)
    }
    if start and stop:
        kwargs['asteroid_condition'] = AsteroidCondition(start, stop)
    _show_resonance_table(integers=integers, **kwargs)


@cli.command(name='planets', help='Shows planets, which exist inside resonance table.')
@click.option('--body-count', default=None, type=click.Choice(['2', '3']),
              help='Example: 2. 2 means two body resonance, 3 means three body resonance,')
def show_planets(body_count: str):
    from resonances.commands import show_planets as _show_planets
    body_count = int(body_count)
    _show_planets(body_count)


@cli.command(help='Generate res files for pointed planets.')
@click.option('--asteroid', '-a', type=int, help='Number of asteroid')
@click.option('--aei-paths', '-p', multiple=True,
              default=(opjoin(PROJECT_DIR, INTEGRATOR_DIR),),
              type=Path(exists=True, resolve_path=True),
              help='path to tar archive contains aei files.'
                   ' Provides downloading from AWS S3 if pointed options access_key,'
                   ' secret_key, bucket in section s3 inside settings file.'
                   ' Example: /etc/aei-1-101.tar.gz')
@click.option('--integers', '-i', default=None, type=str,
              help='Integers are pointing by three values separated by space.'
                   ' Example: \'5 -1 -1\', Example \'1 -1\'', callback=validate_ints)
@click.argument('planets', type=click.Choice(PLANETS), nargs=-1, callback=validate_planets)
def genres(asteroid: int, integers: List[int], aei_paths: Tuple, planets: Tuple):
    from resonances.commands import genres as _genres
    assert integers
    _genres(asteroid, integers, [x for x in aei_paths], planets)


@cli.command(help='Generates resonance table')
@click.argument('planets', type=click.Choice(PLANETS), nargs=-1)
def rtable(planets):
    from resonances.commands import generate_resonance_table
    generate_resonance_table(*planets)
