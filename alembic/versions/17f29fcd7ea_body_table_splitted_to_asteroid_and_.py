"""body table splitted to asteroid and planet

Revision ID: 17f29fcd7ea
Revises: 7bfdf950e9
Create Date: 2015-12-16 01:10:27.618615

"""

# revision identifiers, used by Alembic.
revision = '17f29fcd7ea'
down_revision = '7bfdf950e9'
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY
import sqlalchemy as sa


def upgrade():
    op.drop_column('resonance', 'first_body_id')
    op.drop_column('resonance', 'second_body_id')
    op.drop_column('resonance', 'small_body_id')
    op.drop_column('resonance', 'asteroid_axis')
    op.drop_constraint('uc_name_long_coeff_peri_coeff', 'body')
    op.drop_table('body')

    op.create_table(
        'planet',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('longitude_coeff', sa.Integer, nullable=False),
        sa.Column('perihelion_longitude_coeff', sa.Integer, nullable=False)
    )
    op.create_unique_constraint('uc_name_long_coeff_peri_coeff', 'planet',
                                ['name', 'longitude_coeff', 'perihelion_longitude_coeff'])

    op.create_table(
        'asteroid',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('longitude_coeff', sa.Integer, nullable=False),
        sa.Column('perihelion_longitude_coeff', sa.Integer, nullable=False),
        sa.Column('axis', sa.Float, nullable=False)
    )
    op.create_unique_constraint(
        'uc_name_long_peri_axis', 'asteroid',
        ['name', 'longitude_coeff', 'perihelion_longitude_coeff', 'axis']
    )

    op.add_column('resonance', sa.Column(
        'first_body_id', sa.Integer, sa.ForeignKey('planet.id'), nullable=False
    ))
    op.add_column('resonance', sa.Column(
        'second_body_id', sa.Integer, sa.ForeignKey('planet.id'), nullable=False
    ))
    op.add_column('resonance', sa.Column(
        'small_body_id', sa.Integer, sa.ForeignKey('asteroid.id'), nullable=False
    ))

    op.create_table(
        'phase',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('resonance_id', sa.Integer, sa.ForeignKey('resonance.id'), nullable=False),
        sa.Column('year', sa.Float, nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('is_for_apocentric', sa.Boolean, nullable=False),
    )
    op.create_unique_constraint('uc_time_resonance_id', 'phase',
                                ['resonance_id', 'year', 'is_for_apocentric'])


def downgrade():
    op.drop_constraint('uc_name_long_coeff_peri_coeff', 'planet')
    op.drop_constraint('uc_name_long_peri_axis', 'asteroid')
    op.drop_constraint('uc_time_resonance_id', 'phase')
    op.drop_table('phase')
    op.create_table(
        'body',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('longitude_coeff', sa.Integer, nullable=False),
        sa.Column('perihelion_longitude_coeff', sa.Integer, nullable=False)
    )
    op.create_unique_constraint(
        'uc_name_long_coeff_peri_coeff', 'body',
        ['name', 'longitude_coeff', 'perihelion_longitude_coeff']
    )
    op.drop_column('resonance', 'first_body_id')
    op.drop_column('resonance', 'second_body_id')
    op.drop_column('resonance', 'small_body_id')
    op.add_column('resonance', sa.Column(
        'first_body_id', sa.Integer, sa.ForeignKey('body.id'), nullable=False
    ))
    op.add_column('resonance', sa.Column(
        'second_body_id', sa.Integer, sa.ForeignKey('body.id'), nullable=False
    ))
    op.add_column('resonance', sa.Column(
        'small_body_id', sa.Integer, sa.ForeignKey('body.id'), nullable=False
    ))
    op.add_column('resonance', sa.Column('asteroid_axis', sa.Float, nullable=False))
    op.drop_table('planet')
    op.drop_table('asteroid')
