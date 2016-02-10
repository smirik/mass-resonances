from entities.dbutills import Base
from sqlalchemy import Column, Float


class Epoch(Base):
    __tablename__ = 'epoch'
    start_day = Column('start_day', Float)
    end_day = Column('end_day', Float)
