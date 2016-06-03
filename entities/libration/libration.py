from typing import List

from entities.dbutills import Base
from entities.resonance import ThreeBodyResonance, TwoBodyResonance
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref
from .mixin import LibrationMixin


class Libration(LibrationMixin, Base):
    """
    Class represents libration for three body resonance.
    """
    __tablename__ = 'libration'
    _resonance_id = Column('resonance_id', Integer, ForeignKey('resonance.id'), nullable=False,
                           unique=True)
    _resonance = relationship(ThreeBodyResonance, backref=backref('libration', uselist=False))

    def __init__(self, resonance: ThreeBodyResonance, circulation_breaks: List[float],
                 body_count: int, is_apocentric: bool):
        """
        :param resonance: related three body resonance.
        :param circulation_breaks: Years of breaks in resonant phases of pointed resonance.
        :param body_count:
        :param is_apocentric: flag indicates about swift by Pi (3.14)
        :return:
        """
        super(Libration, self).__init__(circulation_breaks, body_count, is_apocentric)
        self._resonance = resonance

    @hybrid_property
    def resonance(self) -> ThreeBodyResonance:
        return self._resonance


class TwoBodyLibration(LibrationMixin, Base):
    """
    Class represents libration for two body resonance.
    """
    __tablename__ = 'two_body_libration'
    _resonance_id = Column('resonance_id', Integer, ForeignKey('two_body_resonance.id'),
                           nullable=False, unique=True)
    _resonance = relationship(TwoBodyResonance, backref=backref('libration', uselist=False))

    def __init__(self, resonance: TwoBodyResonance, circulation_breaks: List[float],
                 body_count: int, is_apocentric: bool):
        """
        :param resonance: related two body resonance.
        :param circulation_breaks: Years of breaks in resonant phases of pointed resonance.
        :param body_count:
        :param is_apocentric: flag indicates about swift by Pi (3.14)
        :return:
        """
        super(TwoBodyLibration, self).__init__(circulation_breaks, body_count, is_apocentric)
        self._resonance = resonance

    @hybrid_property
    def resonance(self) -> TwoBodyResonance:
        return self._resonance
