import math
from typing import Iterable
from typing import List
from typing import io

from os.path import join as opjoin
from settings import Config
from utils.shortcuts import cutoff_angle

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


class NoCirculationsException(Exception):
    pass


def _get_line_data(file: io.TextIO, do_cutoff_axis: bool)\
        -> Iterable[List[float]]:
    """
    :type file: io.TextIO
    :type do_cutoff_axis: bool
    :rtype : Generator[List[float], None, None]
    """
    for line in file:
        data = [float(x) for x in line.split()]
        if do_cutoff_axis:
            data[1] = cutoff_angle(data[1] + math.pi)

        yield data


def _get_filepath(body_number: int) -> str:
    angle_dir = opjoin(PROJECT_DIR, CONFIG['output']['angle'])
    return opjoin(angle_dir, 'A%i.res' % body_number)


def find_first_circulation(body_number: int, do_cutoff_axis: bool = False) \
        -> float:
    """
    :param int body_number:
    :param bool do_cutoff_axis:
    :raises: NoCirculationsException
    :return:
    """
    file = _get_filepath(body_number)

    with open(file) as f:
        for data in _get_line_data(f, do_cutoff_axis):
            if data[1]:
                return data[0]

    raise NoCirculationsException('No circulations')


def find_circulation(in_filepath: str, do_cutoff_axis: bool = False) -> List[float]:
    """Find circulations in file.

    :param in_filepath: path of file, which contains data for computing circulations.
    :param bool do_cutoff_axis: if true, axises will be converted to interval
    [-Pi; 0) and [0; Pi]
    :rtype: list
    :return: list of circulation breaks.
    :raises FileNotFoundError: if file doesn't exist
    """
    result_breaks = []  # circulation breaks by OX
    p_break = 0

    with open(in_filepath) as f:
        previous_resonant_phase = None
        for data in _get_line_data(f, do_cutoff_axis):
            # If the distance (OY axis) between new point and previous more
            # than PI then there is a break (circulation)
            if data[1]:
                if (previous_resonant_phase and
                        (abs(previous_resonant_phase - data[1]) >= math.pi)):
                    c_break = 1 if (previous_resonant_phase - data[1]) > 0 else -1

                    # For apocentric libration there could be some breaks by
                    # following schema: break on 2*Pi, then break on 2*Pi e.t.c
                    # So if the breaks are on the same value there is no
                    # circulation at this moment
                    if (c_break != p_break) and (p_break != 0):
                        del result_breaks[len(result_breaks) - 1]

                    result_breaks.append(data[0])
                    p_break = c_break

            previous_resonant_phase = data[1]

    return result_breaks
