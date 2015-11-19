from typing import List

from entities import ThreeBodyResonance
from settings import Config

CONFIG = Config.get_params()
LIBRATION_MIN = CONFIG['resonance']['libration']['min']


class Libration:
    """
    Class represents libration.
    """
    APOCENTRIC_ID = 2
    PURE_ID = 1
    APOCENTRIC_PURE_ID = 3
    MIN_BREAKS = 2

    def __init__(self, asteroid_number: int, resonance: ThreeBodyResonance,
                 circulation_breaks: List[float], body_count: int):
        self._resonance = resonance
        self._asteroid_number = asteroid_number
        self._circulation_breaks = circulation_breaks
        self._average_delta = None
        self._percentage = None

        if self._circulation_breaks:
            previous_circulation_break = 0
            libration = 0
            circulation = 0
            average_delta = 0  # medium interval of circulations
            for cir_break in circulation_breaks:
                break_delta = cir_break - previous_circulation_break

                average_delta += break_delta
                if break_delta > LIBRATION_MIN:
                    libration += break_delta
                else:
                    circulation += break_delta
                previous_circulation_break = cir_break

            average_delta /= len(circulation_breaks)
            libration_percent = libration / body_count * 100

            if libration_percent:
                self._average_delta = average_delta
                self._percentage = libration_percent

    @property
    def circulation_breaks(self) -> List[float]:
        return self._circulation_breaks

    @property
    def average_delta(self) -> float:
        return self._average_delta

    @property
    def percentage(self) -> float:
        return self._percentage

    @property
    def max_diff(self) -> float:
        """Computes max difference between pair of circulation breaks.

        :return:
        """
        breaks = self._circulation_breaks
        breaks.append(CONFIG['gnuplot']['x_stop'])
        return max([a - b for a, b in zip(breaks, [0.] + breaks[:-1])])

    @property
    def is_apocentric(self) -> bool:
        return bool(self._circulation_breaks or self._percentage or self._average_delta)

    def __str__(self):
        return u'% = {0:f}%, medium period = {1:f}, max = {2:f}' \
            .format(self._percentage, self._average_delta, self.max_diff)

    @property
    def asteroid_number(self) -> int:
        return self._asteroid_number

    @property
    def resonance(self) -> ThreeBodyResonance:
        return self._resonance

    def as_apocentric(self) -> str:
        return '%i;%s;%i;%f;%f' % (
            self._asteroid_number, str(self._resonance), self.APOCENTRIC_ID,
            self._average_delta, self.max_diff
        )

    @property
    def is_pure(self):
        return len(self._circulation_breaks) < self.MIN_BREAKS

    def as_pure(self) -> str:
        return '%i;%s;%i' % (self._asteroid_number, str(self._resonance),
                             self.PURE_ID)

    def as_pure_apocentric(self) -> str:
        return '%i;%s;%i' % (self._asteroid_number, str(self._resonance),
                             self.APOCENTRIC_PURE_ID)
