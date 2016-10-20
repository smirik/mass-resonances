"""libration.second_planet_name_id libration.first_planet_name_id as required

Revision ID: d31ecc2d0185
Revises: c6b695987112
Create Date: 2016-04-19 00:11:13.644890

"""

# revision identifiers, used by Alembic.
revision = 'd31ecc2d0185'
down_revision = 'c6b695987112'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('libration', 'first_planet_name_id', nullable=False)
    op.alter_column('libration', 'second_planet_name_id', nullable=False)
    op.drop_constraint('libration_resonance_id_key', 'libration')
    op.create_unique_constraint('uc_resonance_planet_names', 'libration',
                                ['resonance_id', 'first_planet_name_id', 'second_planet_name_id'])


def downgrade():
    op.alter_column('libration', 'first_planet_name_id', nullable=True)
    op.alter_column('libration', 'second_planet_name_id', nullable=True)
    op.drop_constraint('uc_resonance_planet_names', 'libration')
    op.create_unique_constraint('libration_resonance_id_key', 'libration', ['resonance_id'])
