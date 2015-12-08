"""create libration field is_apocentric

Revision ID: 7bfdf950e9
Revises: ead96a7a16
Create Date: 2015-12-08 23:18:35.392615

"""

# revision identifiers, used by Alembic.
revision = '7bfdf950e9'
down_revision = 'ead96a7a16'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('libration', sa.Column('is_apocentric', sa.Boolean, nullable=False))


def downgrade():
    op.drop_column('libration', 'is_apocentric')
