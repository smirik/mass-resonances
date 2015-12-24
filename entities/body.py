from entities.dbutills import Base
from sqlalchemy import Column, Integer, String, UniqueConstraint, Float

LONG = 'longitude'
PERI = 'perihelion_%s' % LONG
LONG_COEFF = '%s_coeff' % LONG
PERI_COEFF = '%s_coeff' % PERI

UNIQUE_FIELDS = ('name', 'longitude_coeff', 'perihelion_longitude_coeff')


class _Body(object):
    name = Column(String(255), nullable=False)
    longitude_coeff = Column(Integer, nullable=False)
    perihelion_longitude_coeff = Column(Integer, nullable=False)

    def __getitem__(self, item: str):
        return getattr(self, item)


class Planet(_Body, Base):
    __tablename__ = 'planet'
    __table_args__ = (UniqueConstraint(
        *UNIQUE_FIELDS, name='uc_name_long_coeff_peri_coeff'
    ),)


class Asteroid(_Body, Base):
    __tablename__ = 'asteroid'
    __table_args__ = (UniqueConstraint(
        *UNIQUE_FIELDS, 'axis', name='uc_name_long_peri_axis'
    ),)
    axis = Column(Float, nullable=False)
