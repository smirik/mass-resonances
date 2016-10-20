"""create libration table

Revision ID: ead96a7a16
Revises:
Create Date: 2015-11-26 00:09:14.260740

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = 'ead96a7a16'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'body',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('longitude_coeff', sa.Integer, nullable=False),
        sa.Column('perihelion_longitude_coeff', sa.Integer, nullable=False)
    )
    op.create_unique_constraint('uc_name_long_coeff_peri_coeff', 'body',
                                ['name', 'longitude_coeff', 'perihelion_longitude_coeff'])

    op.create_table(
        'resonance',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('asteroid_axis', sa.Float, nullable=False),
        sa.Column('first_body_id', sa.Integer, sa.ForeignKey('body.id'), nullable=False),
        sa.Column('second_body_id', sa.Integer, sa.ForeignKey('body.id'), nullable=False),
        sa.Column('small_body_id', sa.Integer, sa.ForeignKey('body.id'), nullable=False)
    )
    op.create_unique_constraint('uc_axis_first_second_small', 'resonance', [
        'asteroid_axis', 'first_body_id', 'second_body_id', 'small_body_id'])

    op.create_table(
        'libration',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('resonance_id', sa.Integer, sa.ForeignKey('resonance.id'), nullable=False,
                  unique=True),
        sa.Column('average_delta', sa.Float),
        sa.Column('percentage', sa.Float),
        sa.Column('circulation_breaks', ARRAY(sa.Float), nullable=False),
    )


def downgrade():
    op.drop_table('body')
    op.drop_table('resonance')
    op.drop_table('libration')
