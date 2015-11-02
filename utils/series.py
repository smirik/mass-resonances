import math
from typing import Tuple
from typing import TypeVar
from typing import List
from typing import io
from typing import Generator
from os.path import join as opjoin

from settings import ConfigSingleton
from settings import PROJECT_DIR

CONFIG = ConfigSingleton.get_singleton()
LIBRATION_MIN = CONFIG['resonance']['libration']['min']


class NoCirculationsException(Exception):
    pass


def _cutoff_angle(angle: float) -> float:
    """Cutoff input angle to interval from 0 to 2Pi or from 0 to -2Pi
    if input angle is negative.

    :param float angle:
    :rtype: float
    :return: angle in interval [0; 2Pi] or [0; -2Pi]
    """
    value = angle + math.pi
    subtrahend = 2 * math.pi if value < 0 else 0
    return value % math.pi - subtrahend


def _get_line_data(file: io.TextIO, is_transport: bool) \
        -> Generator[List[float], None, None]:
    """
    :rtype : Generator[List[float], None, None]
    """
    for line in file:
        data = [float(x) for x in line.split()]
        if is_transport:
            data[1] = _cutoff_angle(data[1])

        yield data


def _get_filepath(body_number: int) -> str:
    angle_dir = opjoin(PROJECT_DIR, CONFIG['output']['angle'])
    return opjoin(angle_dir, 'A%i.res' % body_number)


def find_first_circulation(body_number: int, is_transport: bool = False) \
        -> float:
    """
    :param int body_number:
    :param bool is_transport:
    :raises: NoCirculationsException
    :return:
    """
    file = _get_filepath(body_number)

    with open(file) as f:
        for data in _get_line_data(f, is_transport):
            if data[1]:
                return data[0]

    raise NoCirculationsException('No circulations')


T = TypeVar('T', float, None)


def find_circulation(body_number: int, start: int, stop: int,
                     is_transport: bool = False) -> Tuple[List[float], T, T]:
    """Find circulation in data array from key start to key stop.
    Raises NoCirculationsException if there is no circulations.

    :param int body_numbert:
    :param int start:
    :param int stop:
    :param bool transport:
    :rtype: tuple
    :return: list of circulation breaks, percantage of libration, average
    delta between circulation breaks.
    :raises FileNotFoundError: if file doesn't exist
    :raises NoCirculationsException: if number of circulation breaks will less
    than 2
    """
    file = _get_filepath(body_number)
    breaks = []  # circulation breaks by OX
    p_break = 0

    with open(file) as f:
        previous = None
        for data in _get_line_data(f, is_transport):
            # If the distance (OY axis) between new point and previous more
            # than PI then there is a break (circulation)
            if data[1]:
                if previous and (abs(previous - data[1]) >= math.pi):
                    c_break = 1 if (previous - data[1]) > 0 else -1

                    # For apocentric libration there could be some breaks by
                    # following schema: break on 2*Pi, then break on 2*Pi e.t.c
                    # So if the breaks are on the same value there is no
                    # circulation at this moment
                    if (c_break != p_break) and (p_break != 0):
                        del breaks[len(breaks) - 1]

                    breaks.append(data[0])
                    p_break = c_break

            previous = data[1]

    # pure libration if there are no breaks (or just one for apocentric
    # libration e.g.)
    if len(breaks) < 2:
        raise NoCirculationsException('No circulations')
    else:
        previous = 0

        libration = 0
        circulation = 0
        average_delta = 0  # medium interval of circulations

        # Find the libration / circulation intervals
        for x in breaks:
            average_delta += (x - previous)
            if (x - previous) > LIBRATION_MIN:
                libration += (x - previous)
            else:
                circulation += (x - previous)
            previous = x

        average_delta /= len(breaks)
        # years in libration in percents.
        libration_percent = libration / (stop - start) * 100
        if libration_percent:
            return breaks, libration_percent, average_delta
        else:
            return breaks, None, None


def get_max_diff(breaks: List[float]) -> float:
    """Search max difference between pair of elements of list.
    First differents computes from first element of breaks and 0.

    :param list breaks: list of elements
    :rtype: float
    :return: max difference
    """
    breaks.append(CONFIG['gnuplot']['x_stop'])
    return max([a - b for a, b in zip(breaks, [0.] + breaks[:-1])])
