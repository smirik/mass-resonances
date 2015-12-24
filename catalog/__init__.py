import sys
from typing import List
import os
import logging
from entities import ThreeBodyResonance, build_resonance
from entities.dbutills import session
from settings import Config
from .find_resonances import find_resonances

CONFIG = Config.get_params()
SKIP_LINES = CONFIG['catalog']['astdys']['skip']
PROJECT_DIR = Config.get_project_dir()
PATH = os.path.join(PROJECT_DIR, CONFIG['catalog']['file'])
AXIS_COLUMN_NUMBER = 6
AXIS_SWING = CONFIG['resonance']['axis_error']


def find_by_number(number: int) -> List[float]:
    """Find asteroid parameters by number.

    :param int number: num for search.
    :return list: array contains parameters of asteroid.
    """

    try:
        with open(PATH, 'r') as f_file:
            for i, line in enumerate(f_file):
                if i < number - 1 + SKIP_LINES:
                    continue

                arr = line.split()[1:]
                arr = [float(x) for x in arr]
                arr[4], arr[5] = arr[5], arr[4]
                return arr
    except FileNotFoundError as e:
        link = 'http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat'
        logging.error('File from astdys doesn\'t exist try this %s' % link)
        raise e


def _build_resonances(from_filepath: str, for_asteroid_num: int) \
        -> List[ThreeBodyResonance]:
    try:
        with open(from_filepath) as resonance_file:
            asteroid_parameters = find_by_number(for_asteroid_num)
            asteroid_axis = asteroid_parameters[1]
            for line in resonance_file:
                line_data = line.split()
                resonant_asteroid_axis = float(line_data[AXIS_COLUMN_NUMBER])
                if abs(resonant_asteroid_axis - asteroid_axis) <= AXIS_SWING:
                    build_resonance(line_data, for_asteroid_num)
    except FileNotFoundError:
        logging.error('File %s not found. Try command resonance_table.',
                      from_filepath)
        sys.exit(1)

    session.commit()


def save_resonances(from_filepath: str, start_asteroid: int, stop_asteroid: int):
    divider = 2
    toolbar_width = (stop_asteroid + 1 - start_asteroid) // divider
    sys.stdout.write("Build resonances [%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width+1))

    for i in range(start_asteroid, stop_asteroid + 1):
        _build_resonances(from_filepath, i)
        if i % divider == 0:
            sys.stdout.write("#")
            sys.stdout.flush()
    sys.stdout.write("\n")
