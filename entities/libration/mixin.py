from typing import List

from abc import abstractproperty
from settings import Config
from sqlalchemy import Boolean, or_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import func
from sqlalchemy import Column, Float
from entities.resonance import ResonanceMixin

CONFIG = Config.get_params()
LIBRATION_MIN = CONFIG['resonance']['libration']['min']


class LibrationMixin:
    """
    Base class provides base interface.
    """
    PURE_ID = 1
    TRANSIENT_ID = 2
    APOCENTRIC_PURE_ID = 3
    MIN_BREAKS = 2

    _average_delta = Column('average_delta', Float)
    _percentage = Column('percentage', Float)
    _circulation_breaks = Column('circulation_breaks', ARRAY(Float), nullable=False)
    _is_apocentric = Column('is_apocentric', Boolean, nullable=False)

    def __init__(self, circulation_breaks: List[float], body_count: int, is_apocentric: bool):
        """
        :param circulation_breaks: time marks, when line on plot is breaked. For example line goes
        down and it ends on bottom border, after this it is begins from top border. Rather line goes
        up and is breaked on top and begins from bottom of plot.
        :param body_count: not correct name. It is end point of time interval. In the case it is
        100000.
        :param is_apocentric:
        :return:
        """
        self._is_apocentric = is_apocentric
        self._circulation_breaks = circulation_breaks

        self._average_delta = None
        self._percentage = None
        """Libration's ratio of interval of the resonant phases that (interval) was outside to
        X_STOP"""
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

    @hybrid_property
    def is_apocentric(self) -> bool:
        return self._is_apocentric

    @property
    def circulation_breaks(self) -> List[float]:
        return self._circulation_breaks

    @property
    def average_delta(self) -> float:
        return self._average_delta

    @property
    def percentage(self) -> float:
        """Libration's ratio of interval of the resonant phases that (interval) was outside to
        X_STOP"""
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
    def is_transient(self) -> bool:
        return bool(self._circulation_breaks or self._percentage or self._average_delta)

    def __str__(self):
        return u'% = {0:f}%, medium period = {1:f}, max = {2:f}' \
            .format(self._percentage, self._average_delta, self.max_diff)

    @hybrid_property
    def is_pure(self):
        return len(self._circulation_breaks) < self.MIN_BREAKS

    @is_pure.expression
    def is_pure(cls):
        res = or_(func.array_length(cls._circulation_breaks, 1) < cls.MIN_BREAKS,
                  func.array_length(cls._circulation_breaks, 1).is_(None))
        return res

    @property
    def asteroid_number(self) -> int:
        name = self.resonance.small_body.name
        return int(name[1:])

    @abstractproperty
    def resonance(self) -> ResonanceMixin:
        pass

    def as_transient(self) -> str:
        return '%i;%s;%i;%f;%f' % (
            self.asteroid_number, str(self.resonance), self.TRANSIENT_ID,
            self._average_delta, self.max_diff
        )

    def as_pure(self) -> str:
        return '%s;%s;%i' % (self.asteroid_number, str(self.resonance),
                             self.PURE_ID)

    def as_pure_apocentric(self) -> str:
        return '%s;%s;%i' % (self.asteroid_number, str(self.resonance),
                             self.APOCENTRIC_PURE_ID)


