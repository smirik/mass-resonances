"""add table with asteroids, that have broken aei

Revision ID: 53265c28c53
Revises: 17f29fcd7ea
Create Date: 2016-03-09 18:37:40.884054

"""

# revision identifiers, used by Alembic.
revision = '53265c28c53'
down_revision = '17f29fcd7ea'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'broken_asteroid',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.UniqueConstraint('name')
    )


def downgrade():
    op.drop_table('broken_asteroid')
