from entities import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref


class Phase(Base):
    __tablename__ = 'phase'

    id = sa.Column(sa.Integer, primary_key=True)
    resonance_id = sa.Column(sa.Integer, sa.ForeignKey('resonance.id'), nullable=False)
    resonance = relationship('ThreeBodyResonance', foreign_keys=resonance_id,
                             backref=backref('phases'))
    year = sa.Column(sa.Float, nullable=False)
    value = sa.Column(sa.Float, nullable=False)
    is_for_apocentric = sa.Column(sa.Boolean, nullable=False)

    __table_args__ = (sa.UniqueConstraint(
        'resonance_id', 'year', 'is_for_apocentric', name='uc_time_resonance_id'
    ),)
