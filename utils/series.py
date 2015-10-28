import math
from typing import Tuple
from os.path import join as opjoin

from settings import ConfigSingleton
from settings import PROJECT_DIR

CONFIG = ConfigSingleton.get_singleton()


class NoCirculationsException(Exception):
    pass


def find_circulation(body_number: int, start: int, stop: int,
                     transport: bool = False, find_all: bool = False) -> Tuple:
    """Find circulation in data array from key start to key stop.
    raises NoCirculationsException if there is no circulations

    :param body_number int:
    :param start int:
    :param stop int:
    :param transport bool:
    :param find_all bool:
    :rtype: int
    :return: position of break (or array of positions) if exists.
    :raises: FileNotFoundError
    :raises: NoCirculationsException
    """

    angle_dir = opjoin(PROJECT_DIR, CONFIG['output']['angle'])
    file = opjoin(angle_dir, 'A%i.res' % body_number)

    data = []
    breaks = []  # circulation breaks by OX
    previous = []

    libration_min = CONFIG['resonance']['libration']['min']

    c_break = 0
    p_break = 0
    pp_break = 0

    with open(file) as f:
        for line in f:
            data = [float(x) for x in line.split()]
            # For apocentric libration resonant angle is increased on PI
            if transport:
                value = data[1] + math.pi
                subtrahend = 2 * math.pi if value < 0 else 0
                data[1] = value % math.pi - subtrahend

            # If the distance (OY axis) between new point and previous more
            # than PI then there is a break (circulation)
            if data[1]:
                if previous and (abs(previous - data[1]) >= math.pi):
                    if not find_all:
                        return data[0]

                    if (previous - data[1]) > 0:
                        c_break = 1
                    else:
                        c_break = -1

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
    if len(breaks.size) < 2:
        raise NoCirculationsException('No circulations')
    else:
        previous = 0

        libration = 0
        circulation = 0
        delta = 0  # medium interval of circulations

        # Find the libration / circulation intervals
        for x in breaks:
            delta += (x - previous)
            if (x - previous) > libration_min:
                libration += (x - previous)
            else:
                circulation += (x - previous)
            previous = x

        delta /= len(breaks)
        libration_percent = libration / (stop - start) * 100  # years in libration in percents
        if libration_percent:
            return breaks, libration_percent, delta
        else:
            return breaks, False, False
