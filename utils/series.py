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


class CirculationYearsFinder:
    def __init__(self, for_apocentric: bool, in_filepath: str):
        self._in_filepath = in_filepath
        self._for_apocentric = for_apocentric

    def get_years(self) -> List[float]:
        """Find circulations in file.
        """
        result_breaks = []  # circulation breaks by OX
        p_break = 0

        with open(self._in_filepath) as f:
            previous_resonant_phase = None
            for years, resonant_phase in self._get_line_data(f):
                # If the distance (OY axis) between new point and previous more
                # than PI then there is a break (circulation)
                if resonant_phase:
                    if (previous_resonant_phase and
                            (abs(previous_resonant_phase - resonant_phase) >= math.pi)):
                        c_break = 1 if (previous_resonant_phase - resonant_phase) > 0 else -1

                        # For apocentric libration there could be some breaks by
                        # following schema: break on 2*Pi, then break on 2*Pi e.t.c
                        # So if the breaks are on the same value there is no
                        # circulation at this moment
                        if (c_break != p_break) and (p_break != 0):
                            del result_breaks[len(result_breaks) - 1]

                        result_breaks.append(years)
                        p_break = c_break

                previous_resonant_phase = resonant_phase

        return result_breaks

    def get_first_years(self) -> float:
        """
        :param int body_number:
        :return:
        """
        with open(self._in_filepath) as f:
            for years, resonant_phase in self._get_line_data(f):
                if resonant_phase:
                    return years

    def _get_line_data(self, file: io.TextIO) -> Iterable[List[float]]:
        """
        :type file: io.TextIO
        :rtype : Generator[List[float], None, None]
        """
        for line in file:
            data = [float(x) for x in line.split()]
            if self._for_apocentric:
                data[1] = cutoff_angle(data[1] + math.pi)

            years = data[0]
            resonant_phase = data[1]
            yield years, resonant_phase
