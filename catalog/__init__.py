import logging
import sys
from typing import List, Tuple

import os
from entities import ThreeBodyResonance, build_resonance, BodyNumberEnum
from entities import get_resonance_factory
from settings import Config

CONFIG = Config.get_params()
SKIP_LINES = CONFIG['catalog']['astdys']['skip']
PROJECT_DIR = Config.get_project_dir()
PATH = os.path.join(PROJECT_DIR, CONFIG['catalog']['file'])
AXIS_SWING = CONFIG['resonance']['axis_error']
AXIS_COLUMNS = {BodyNumberEnum.two: 4, BodyNumberEnum.three: 6}


def find_by_number(number: int) -> List[float]:
    """Find asteroid parameters by number in catalog.

    :param int number: num for search.
    :return: list contains parameters of asteroid.
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


def build_possible_resonances(from_filepath: str, for_asteroid_num: int, planets: Tuple[str]) \
        -> List[ThreeBodyResonance]:
    """
    Builds resonances, that can be for pointed asteroid. Resonance is considering if it's semi major
    axis similar to semi major axis of asteroid from catalog. Them compares with some swing, which
    which pointed in settings.
    :param planets:
    :param from_filepath: filepath to catalog of asteroids.
    :param for_asteroid_num: number of asteroid.
    :return: list of resonances.
    """
    res = []
    try:
        with open(from_filepath) as resonance_file:
            asteroid_parameters = find_by_number(for_asteroid_num)
            asteroid_axis = asteroid_parameters[1]
            for line in resonance_file:
                line_data = line.split()

                body_count = BodyNumberEnum(len(planets) + 1)
                assert (body_count == BodyNumberEnum.three and len(line_data) > 5 or
                        body_count == BodyNumberEnum.two)
                resonant_asteroid_axis = float(line_data[AXIS_COLUMNS[body_count]])
                if abs(resonant_asteroid_axis - asteroid_axis) <= AXIS_SWING:
                    resonance_factory = get_resonance_factory(planets, line_data,
                                                              for_asteroid_num)
                    res.append(build_resonance(resonance_factory))
    except FileNotFoundError:
        logging.error('File %s not found. Try command resonance_table.',
                      from_filepath)
        sys.exit(1)

    return res
