import logging
import sys
from typing import List

import os
from catalog import AstDys
from mercury_bridge import calc
from settings import ConfigSingleton
from settings import PROJECT_DIR
from storage import ResonanceDatabase
from storage.resonance_archive import extract
from utils.series import find_circulation, NoCirculationsException
from utils.series import get_max_diff

CONFIG = ConfigSingleton.get_singleton()
X_STOP = CONFIG['gnuplot']['x_stop']
AXIS_SWING = CONFIG['resonance']['axis_error']
RESONANCE_TABLE_FILE = CONFIG['resonance_table']['file']
RESONANCE_FILE = os.path.join(PROJECT_DIR, 'axis', RESONANCE_TABLE_FILE)


def _get_resonances(by_asteroid_axis: float, with_swing: float)\
        -> List[List[float]]:
    res = []
    try:
        with open(RESONANCE_FILE) as f:
            for line in f:
                resonance = [float(x) for x in line.split()]
                if abs(resonance[6] - by_asteroid_axis) <= with_swing:
                    res.append(resonance)
    except FileNotFoundError:
        logging.error('File %s not found. Try command resonance_table.' %
                      RESONANCE_FILE)
        sys.exit(1)

    return res


def _find_resonance_with_min_axis(by_axis: float, with_swing: float = 0.0001)\
        -> List[float]:
    resonances = _get_resonances(by_axis, with_swing)
    index_of_min_axis = 0

    def _delta(of_resonance: List[float]) -> float:
        return of_resonance[6] - by_axis

    for i, resonance in enumerate(resonances):
        if _delta(resonance) < _delta(resonances[index_of_min_axis]):
            index_of_min_axis = i

    return resonances[index_of_min_axis]


def _find_resonances(by_axis: float, with_swing: float = 0.0001) \
        -> List[List[float]]:
    """Find resonances from /axis/resonances by asteroid axis. Currently
    described by 7 items list of floats. 6 is integers satisfying
    D'Alembert rule. First 3 for longitutes, and second 3 for longitutes
    perihilion. Seventh value is asteroid axis.
    :param by_axis:
    :param with_swing:
    :return:
    """
    return _get_resonances(by_axis, with_swing)


def find(start: int, stop: int, is_current: bool = False):
    """Find all possible resonances for all asteroids from start to stop.

    :param is_current:
    :param stop:
    :param start:
    :return:
    """
    resonances = []
    delta = stop - start

    logging.info("Finding asteroids and possible resonances")
    for i in range(delta + 1):
        num = start + i
        arr = AstDys.find_by_number(num)
        resonances.append(_find_resonances(arr[1], AXIS_SWING))

    rdb = ResonanceDatabase('export/full.db')
    if not is_current:
        try:
            extract(start)
        except FileNotFoundError as e:
            logging.info('Archive %s not found. Try command \'package\'' % e.filename)

    for i in range(delta + 1):
        asteroid_num = start + i
        if resonances[i]:
            for resonance in resonances[i]:
                logging.debug("Check asteroid %i" % asteroid_num)
                calc(asteroid_num, resonance)

                try:
                    breaks, libration_percent, average_delta = find_circulation(
                        asteroid_num, 0, X_STOP, False)
                    # apocentric libration
                    if breaks or libration_percent or average_delta:
                        max_diff = get_max_diff(breaks)
                        if libration_percent:
                            logging.info(
                                'A%i, % = %f%, medium period = %f, max = %f, resonance = %s' % (
                                    asteroid_num, libration_percent, average_delta,
                                    max_diff, str(resonance)
                                )
                            )
                            s = '%i;%s;2;%f;%f' % (asteroid_num, str(resonance),
                                                   average_delta, max_diff)
                            rdb.add_string(s)
                        else:
                            logging.debug('A%i, NO RESONANCE, resonance = %s, max = %f' % (
                                asteroid_num, str(resonance), max_diff
                            ))
                except NoCirculationsException:
                    logging.info('A%i, pure resonance %s' % (asteroid_num, str(resonance)))
                    s = '%i;%s;1' % (asteroid_num, str(resonance))
                    rdb.add_string(s)
                try:
                    find_circulation(asteroid_num, 0, X_STOP, True)
                except NoCirculationsException:
                    logging.info('A%i, pure apocentric resonance %s' % (
                        asteroid_num, str(resonance)
                    ))
                    s = '%i;%s;3' % (asteroid_num, str(resonance))
                    rdb.add_string(s)
