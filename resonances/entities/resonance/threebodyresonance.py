from typing import Dict, List

from resonances.entities.dbutills import Base
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship, backref

from resonances.entities.body import LONG
from resonances.entities.body import PERI
from resonances.entities.body import Planet
from .resonancemixin import ResonanceMixin, ResonanceTableOptions


class ThreeBodyResonance(ResonanceMixin, Base):
    """ Represents three body resonance. Stores coeffitients that satisfy rule
    D'Alambert and axis of related asteroid.
    """
    BUILDER = ResonanceTableOptions([10, 10, 10, 30], [
        'First planet', 'Second planet', 'Asteroid',
        'Integers and semi major axis of asteroid'])

    @classmethod
    def get_table_options(cls) -> ResonanceTableOptions:
        return cls.BUILDER

    __tablename__ = 'resonance'
    __table_args__ = (UniqueConstraint(
        'first_body_id', 'second_body_id', 'small_body_id',
        name='uc_first_second_small'
    ),)

    @classmethod
    def _small_body_ref(cls):
        return backref('resonances')

    second_body_id = Column(Integer, ForeignKey('planet.id'), nullable=False)
    second_body = relationship('Planet', foreign_keys=second_body_id)  # type: Planet

    def get_big_bodies(self) -> List[Planet]:
        return [self.first_body, self.second_body]

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
