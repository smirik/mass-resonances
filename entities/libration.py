from typing import List

from entities.body import PlanetName
from entities.dbutills import Base
from settings import Config
from sqlalchemy import Boolean, UniqueConstraint
from sqlalchemy import Column, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref
from .threebodyresonance import ThreeBodyResonance


CONFIG = Config.get_params()
LIBRATION_MIN = CONFIG['resonance']['libration']['min']


class Libration(Base):
    """
    Class represents libration.
    """
    PURE_ID = 1
    TRANSIENT_ID = 2
    APOCENTRIC_PURE_ID = 3
    MIN_BREAKS = 2

    __tablename__ = 'libration'
    __table_args__ = (UniqueConstraint('resonance_id', 'first_planet_name_id',
                                       'second_planet_name_id', name='uc_resonance_planet_names'),)
    _resonance_id = Column('resonance_id', Integer, ForeignKey('resonance.id'), nullable=False)
    _resonance = relationship(ThreeBodyResonance, backref=backref('librations', uselist=True))
    _average_delta = Column('average_delta', Float)
    _percentage = Column('percentage', Float)
    _circulation_breaks = Column('circulation_breaks', ARRAY(Float), nullable=False)
    _is_apocentric = Column('is_apocentric', Boolean, nullable=False)

    _first_planet_name_id = Column('first_planet_name_id', Integer, ForeignKey('planet_name.id'),
                                   nullable=False)

    first_planet_name = relationship(PlanetName, backref=backref('librations', uselist=True),
                                     foreign_keys=_first_planet_name_id)
    _second_planet_name_id = Column('second_planet_name_id', Integer, ForeignKey('planet_name.id'),
                                    nullable=False)
    second_planet_name = relationship(PlanetName, backref=backref('librations2', uselist=True),
                                      foreign_keys=_second_planet_name_id)

    def __init__(self, resonance: ThreeBodyResonance, circulation_breaks: List[float],
                 body_count: int, is_apocentric: bool,
                 first_planet_name: PlanetName, second_planet_name: PlanetName):
        """
        :param resonance: related resonance.
        :param circulation_breaks: Years of breaks in resonant phases of pointed resonance.
        :param body_count:
        :param is_apocentric: flag indicates about swift by Pi (3.14)
        :param first_planet_name:
        :param second_planet_name:
        :return:
        """
        self.second_planet_name = second_planet_name
        self._second_planet_name_id = second_planet_name.id
        self.first_planet_name = first_planet_name
        self._first_planet_name_id = first_planet_name.id

        self._is_apocentric = is_apocentric
        self._resonance = resonance
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

    @property
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

    @property
    def asteroid_number(self) -> int:
        name = self._resonance.small_body.name
        return int(name[1:])

    @hybrid_property
    def resonance(self) -> ThreeBodyResonance:
        return self._resonance

    def as_transient(self) -> str:
        return '%i;%s;%i;%f;%f' % (
            self.asteroid_number, str(self._resonance), self.TRANSIENT_ID,
            self._average_delta, self.max_diff
        )

    @property
    def is_pure(self):
        return len(self._circulation_breaks) < self.MIN_BREAKS

    def as_pure(self) -> str:
        return '%s;%s;%i' % (self.asteroid_number, str(self._resonance),
                             self.PURE_ID)

    def as_pure_apocentric(self) -> str:
        return '%s;%s;%i' % (self.asteroid_number, str(self._resonance),
                             self.APOCENTRIC_PURE_ID)

    @hybrid_property
    def first_planet_name_id(self):
        return self._first_planet_name_id

    @hybrid_property
    def second_planet_name_id(self):
        return self._second_planet_name_id

