import sqlalchemy as sa
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship

from resonances.entities import Base


class Phase(Base):
    __tablename__ = 'phase'

    id = sa.Column(sa.Integer, primary_key=True)
    resonance_id = sa.Column(sa.Integer, sa.ForeignKey('resonance.id'), nullable=False)
    resonance = relationship('ThreeBodyResonance', foreign_keys=resonance_id,
                             backref=backref('phases'))
    year = sa.Column(sa.Float, nullable=False)
    value = sa.Column(sa.Float, nullable=False)

    __table_args__ = (sa.UniqueConstraint(
        'resonance_id', 'year', name='uc_time_resonance_id'
    ),)
