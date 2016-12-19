from sqlalchemy import Column, Integer, String, UniqueConstraint, Float, func, cast
from sqlalchemy.ext.hybrid import hybrid_property

from resonances.entities.dbutills import Base

LONG = 'longitude'
PERI = 'perihelion_%s' % LONG
LONG_COEFF = '%s_coeff' % LONG
PERI_COEFF = '%s_coeff' % PERI

UNIQUE_FIELDS = ('name', 'longitude_coeff', 'perihelion_longitude_coeff')


class _Body(object):
    name = Column(String(255), nullable=False)
    longitude_coeff = Column(Integer, nullable=False)
    perihelion_longitude_coeff = Column(Integer, nullable=False)

    def __str__(self):
        return '%i %i' % (self.longitude_coeff, self.perihelion_longitude_coeff)


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

    @hybrid_property
    def number(self) -> int:
        return int(self.name[1:])

    @number.expression
    def number(cls):
        return cast(func.substr(cls.name, 2, func.length(cls.name) - 1), Integer)

    def __str__(self):
        return '%s %f' % (super(Asteroid, self).__str__(), self.axis)


class BrokenAsteroid(Base):
    __tablename__ = 'broken_asteroid'
    __table_args__ = (UniqueConstraint('name'),)
    name = Column(String(255), nullable=False)
    reason = Column(String(255), nullable=True)
