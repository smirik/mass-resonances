"""Addition two body libration

Revision ID: cc46f63dab
Revises: 6f1cc0cea415
Create Date: 2016-06-01 05:16:37.588376

"""

# revision identifiers, used by Alembic.
revision = 'cc46f63dab'
down_revision = '6f1cc0cea415'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


def upgrade():
    op.create_table(
        'two_body_libration',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('resonance_id', sa.Integer, sa.ForeignKey('two_body_resonance.id'),
                  nullable=False, unique=True),
        sa.Column('average_delta', sa.Float),
        sa.Column('percentage', sa.Float),
        sa.Column('circulation_breaks', ARRAY(sa.Float), nullable=False),
        sa.Column('is_apocentric', sa.Boolean, nullable=False)
    )


def downgrade():
    op.drop_table('two_body_libration')
