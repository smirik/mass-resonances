from entities.dbutills import Base
from sqlalchemy import Column, Integer, String, UniqueConstraint

LONG = 'longitude'
PERI = 'perihelion_%s' % LONG
LONG_COEFF = '%s_coeff' % LONG
PERI_COEFF = '%s_coeff' % PERI


class Body(Base):
    __tablename__ = 'body'
    __table_args__ = (UniqueConstraint(
        'name', 'longitude_coeff', 'perihelion_longitude_coeff',
        name='uc_name_long_coeff_peri_coeff'
    ),)
    name = Column(String(255), nullable=False)
    longitude_coeff = Column(Integer, nullable=False)
    perihelion_longitude_coeff = Column(Integer, nullable=False)

    def __getitem__(self, item: str):
        return getattr(self, item)
