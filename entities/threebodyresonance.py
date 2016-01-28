from typing import Dict
from typing import List

from entities.body import LONG
from entities.body import PERI
from entities.body import LONG_COEFF
from entities.body import PERI_COEFF
from entities.body import Planet
from entities.body import Asteroid
from entities.dbutills import Base
from entities.dbutills import get_or_create
from sqlalchemy import Column, Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property


class ThreeBodyResonance(Base):
    """ Represents three body resonance. Stores coeffitients that satisfy rule
    D'Alambert and axis of related asteroid.
    """
    __tablename__ = 'resonance'
    __table_args__ = (UniqueConstraint(
        'first_body_id', 'second_body_id', 'small_body_id',
        name='uc_axis_first_second_small'
    ),)

    first_body_id = Column(Integer, ForeignKey('planet.id'), nullable=False)
    first_body = relationship('Planet', foreign_keys=first_body_id)  # type: Planet
    second_body_id = Column(Integer, ForeignKey('planet.id'), nullable=False)
    second_body = relationship('Planet', foreign_keys=second_body_id)  # type: Planet
    small_body_id = Column(Integer, ForeignKey('asteroid.id'), nullable=False)
    small_body = relationship('Asteroid', foreign_keys=small_body_id,  # type: Asteroid
                              backref=backref('resonances'))

    @hybrid_property
    def asteroid_axis(self):
        return self.small_body.axis

    @hybrid_property
    def asteroid_number(self) -> int:
        name = self.small_body.name
        return int(name[1:])

    def __str__(self):
        return '[%i %i %i %i %i %i %f]' % (
            self.first_body.longitude_coeff,
            self.second_body.longitude_coeff,
            self.small_body.longitude_coeff,
            self.first_body.perihelion_longitude_coeff,
            self.second_body.perihelion_longitude_coeff,
            self.small_body.perihelion_longitude_coeff,
            self.small_body.axis
        )

    def compute_resonant_phase(self, first_body: Dict[str, float],
                               second_body: Dict[str, float],
                               small_body: Dict[str, float]) -> float:
        """Computes resonant phase by linear combination of coeffitients
        satisfying D'Alambert rule and pointed longitudes.

        :param first_body:
        :param second_body:
        :param small_body:
        :return:
        """
        return (self.first_body.longitude_coeff * first_body[LONG] +
                self.first_body.perihelion_longitude_coeff * first_body[PERI] +
                self.second_body.longitude_coeff * second_body[LONG] +
                self.second_body.perihelion_longitude_coeff * second_body[PERI] +
                self.small_body.longitude_coeff * small_body[LONG] +
                self.small_body.perihelion_longitude_coeff * small_body[PERI])


def build_resonance(data: List[str], asteroid_num: int) -> ThreeBodyResonance:
    """Builds instance of ThreeBodyResonance by passed list of string values.

    :param asteroid_num:
    :param data:
    :return:
    """
    first_body = {
        'name': 'JUPITER',
        LONG_COEFF: int(data[0]),
        PERI_COEFF: int(data[3])
    }
    second_body = {
        'name': 'SATURN',
        LONG_COEFF: int(data[1]),
        PERI_COEFF: int(data[4])
    }
    small_body = {
        'name': 'A%i' % asteroid_num,
        LONG_COEFF: int(data[2]),
        PERI_COEFF: int(data[5]),
        'axis': float(data[6])
    }

    first_body, is_new = get_or_create(Planet, **first_body)
    second_body, is_new = get_or_create(Planet, **second_body)
    small_body, is_new = get_or_create(Asteroid, **small_body)

    resonance, is_new = get_or_create(
        ThreeBodyResonance, first_body=first_body, second_body=second_body,
        small_body=small_body)
    return resonance
