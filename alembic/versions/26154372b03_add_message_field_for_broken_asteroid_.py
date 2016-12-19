"""Add message field for broken_asteroid table.

Revision ID: 26154372b03
Revises: cc46f63dab
Create Date: 2016-12-19 17:22:01.859118

"""

# revision identifiers, used by Alembic.
revision = '26154372b03'
down_revision = 'cc46f63dab'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('broken_asteroid', sa.Column('reason', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('broken_asteroid', 'reason')
