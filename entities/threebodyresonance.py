from typing import Dict
from typing import List

from entities.body import Body, LONG, PERI, LONG_COEFF, PERI_COEFF
from entities.dbutills import Base, session, get_or_create
from sqlalchemy import Column, ForeignKey, Integer, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


class ThreeBodyResonance(Base):
    """ Represents three body resonance. Stores coeffitients that satisfy rule
    D'Alambert and axis of related asteroid.
    """
    __tablename__ = 'resonance'
    __table_args__ = (UniqueConstraint(
        'asteroid_axis', 'first_body_id', 'second_body_id', 'small_body_id',
        name='uc_axis_first_second_small'
    ),)

    asteroid_axis = Column(Float, nullable=False)
    first_body_id = Column(Integer, ForeignKey('body.id'), nullable=False)
    first_body = relationship('Body', foreign_keys=first_body_id)
    second_body_id = Column(Integer, ForeignKey('body.id'), nullable=False)
    second_body = relationship('Body', foreign_keys=second_body_id)
    small_body_id = Column(Integer, ForeignKey('body.id'), nullable=False)
    small_body = relationship('Body', foreign_keys=small_body_id)

    @hybrid_property
    def asteroid_number(self) -> int:
        name = self.small_body.name
        return int(name[1:])

    # @asteroid_number.expression
    # def asteroid_number(cls):
    #     try:
    #         name = str(Body.name)
    #         return int(name[1:])
    #     except ValueError:
    #         return None

    def __str__(self):
        return '[%i %i %i %i %i %i %f]' % (
            self.first_body[LONG_COEFF],
            self.second_body[LONG_COEFF],
            self.small_body[LONG_COEFF],
            self.first_body[PERI_COEFF],
            self.second_body[PERI_COEFF],
            self.small_body[PERI_COEFF],
            self.asteroid_axis
        )

    def get_resonant_phase(self, first_body: Dict[str, float],
                           second_body: Dict[str, float],
                           small_body: Dict[str, float]) -> float:
        """Computes resonant phase by linear combination of stored coeffitients
        and pointed longitudes.

        :param first_body:
        :param second_body:
        :param small_body:
        :return:
        """
        return (self.first_body[LONG_COEFF] * first_body[LONG] +
                self.first_body[PERI_COEFF] * first_body[PERI] +
                self.second_body[LONG_COEFF] * second_body[LONG] +
                self.second_body[PERI_COEFF] * second_body[PERI] +
                self.small_body[LONG_COEFF] * small_body[LONG] +
                self.small_body[PERI_COEFF] * small_body[PERI])


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
        PERI_COEFF: int(data[5])
    }

    first_body, is_new = get_or_create(Body, **first_body)
    second_body, is_new = get_or_create(Body, **second_body)
    small_body, is_new = get_or_create(Body, **small_body)

    resonance, is_new = get_or_create(ThreeBodyResonance, first_body=first_body,
                                      second_body=second_body, small_body=small_body,
                                      asteroid_axis=float(data[6]))
    return resonance
