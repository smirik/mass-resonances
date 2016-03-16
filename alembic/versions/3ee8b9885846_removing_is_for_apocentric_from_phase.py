"""removing is_for_apocentric from phase

Revision ID: 3ee8b9885846
Revises: 53265c28c53
Create Date: 2016-03-16 17:12:44.021218

"""

# revision identifiers, used by Alembic.
revision = '3ee8b9885846'
down_revision = '53265c28c53'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('uc_time_resonance_id', 'phase')
    op.drop_column('phase', 'is_for_apocentric')
    op.create_unique_constraint('uc_time_resonance_id', 'phase', ['resonance_id', 'year'])


def downgrade():
    op.drop_constraint('uc_time_resonance_id', 'phase')
    sa.Column('is_for_apocentric', sa.Boolean, nullable=False),
    op.create_unique_constraint('uc_time_resonance_id', 'phase',
                                ['resonance_id', 'year', 'is_for_apocentric'])
