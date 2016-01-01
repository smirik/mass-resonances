import math
from typing import List
from entities.dbutills import session
from entities.phase import Phase
from settings import Config
from utils.shortcuts import cutoff_angle

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


class NoPhaseException(Exception):
    pass


class CirculationYearsFinder:
    def __init__(self, resonance_id: int, is_for_apocentric: bool):
        self._is_for_apocentric = is_for_apocentric
        self._resonance_id = resonance_id

    def get_years(self) -> List[float]:
        """Find circulations in file.
        """
        result_breaks = []  # circulation breaks by OX
        p_break = 0
        previous_resonant_phase = None
        prev_year = None

        phases = session.query(Phase).filter_by(
            resonance_id=self._resonance_id,
            is_for_apocentric=self._is_for_apocentric
        ).order_by(Phase.year).yield_per(1000).all()
        if not phases:
            raise NoPhaseException('no resonant phases for resonance_id' %
                                   self._resonance_id)
        for phase in phases:  # type: Phase
            # If the distance (OY axis) between new point and previous more
            # than PI then there is a break (circulation)
            if self._is_for_apocentric:
                resonant_phase = cutoff_angle(phase.value + math.pi)
            else:
                resonant_phase = phase.value
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

                    assert prev_year is not None
                    result_breaks.append(prev_year)
                    p_break = c_break

            previous_resonant_phase = resonant_phase
            prev_year = phase.year

        return result_breaks

    # def get_first_years(self) -> float:
    #     """
    #     :return:
    #     """
    #     with open(self._in_filepath) as f:
    #         for years, resonant_phase in self._get_line_data():
    #             if resonant_phase:
    #                 return years

