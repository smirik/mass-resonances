from typing import List
from abc import abstractmethod
from entities.body import Planet
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy import Column
from sqlalchemy.ext.declarative.base import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship


class ResonanceTableOptions:
    """
    class makes table for instance of implementation of class ResonanceMixin
    """

    def __init__(self, column_widths: List[int], column_names: List[str]):
        self.column_names = column_names
        self.column_widths = column_widths

    def get_data(self, from_resonance: 'ResonanceMixin'):
        return [x.name for x in from_resonance.get_big_bodies()] + \
               [from_resonance.small_body.name, from_resonance]


class ResonanceMixin:
    id = Column(Integer, primary_key=True)

    @classmethod
    def _small_body_ref(cls):
        raise NotImplementedError

    @declared_attr
    def first_body_id(cls):
        return Column(Integer, ForeignKey('planet.id'), nullable=False)

    @declared_attr
    def first_body(cls) -> Planet:
        return relationship('Planet', foreign_keys=cls.first_body_id)

    @declared_attr
    def small_body_id(cls):
        return Column(Integer, ForeignKey('asteroid.id'), nullable=False)

    @declared_attr
    def small_body(cls):
        return relationship('Asteroid', foreign_keys=cls.small_body_id,
                            backref=cls._small_body_ref())

    @hybrid_property
    def asteroid_axis(self):
        return self.small_body.axis

    @hybrid_property
    def asteroid_number(self) -> int:
        return int(self.small_body.name[1:])

    @abstractmethod
    def compute_resonant_phase(self, *args) -> float:
        pass

    @abstractmethod
    def get_big_bodies(self) -> List[Planet]:
        pass

    @classmethod
    @abstractmethod
    def get_table_options(cls) -> ResonanceTableOptions:
        pass
