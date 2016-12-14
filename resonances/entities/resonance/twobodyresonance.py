from typing import Dict, List

from resonances.entities.dbutills import Base
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import backref

from resonances.entities.body import LONG, Planet
from resonances.entities.body import PERI
from .resonancemixin import ResonanceMixin, ResonanceTableOptions


class TwoBodyResonance(ResonanceMixin, Base):
    BUILDER = ResonanceTableOptions([10, 10, 30], ['First planet', 'Asteroid',
                                                   'Integers and semi major axis of asteroid'])

    @classmethod
    def get_table_options(cls) -> ResonanceTableOptions:
        return cls.BUILDER

    @classmethod
    def _small_body_ref(cls):
        return backref('two_body_resonances')

    __tablename__ = 'two_body_resonance'
    __table_args__ = (
        UniqueConstraint('first_body_id', 'small_body_id', name='uc_first_small'),)

    def get_big_bodies(self) -> List[Planet]:
        return [self.first_body]

    def __str__(self):
        return '[%i %i %i %i %f]' % (
            self.first_body.longitude_coeff,
            self.small_body.longitude_coeff,
            self.first_body.perihelion_longitude_coeff,
            self.small_body.perihelion_longitude_coeff,
            self.small_body.axis
        )

    def compute_resonant_phase(self, first_body: Dict[str, float],
                               small_body: Dict[str, float]) -> float:
        """Computes resonant phase by linear combination of coeffitients
        satisfying D'Alambert rule and pointed longitudes.

        :param first_body:
        :param small_body:
        :return:
        """
        return (self.first_body.longitude_coeff * first_body[LONG] +
                self.first_body.perihelion_longitude_coeff * first_body[PERI] +
                self.small_body.longitude_coeff * small_body[LONG] +
                self.small_body.perihelion_longitude_coeff * small_body[PERI])
