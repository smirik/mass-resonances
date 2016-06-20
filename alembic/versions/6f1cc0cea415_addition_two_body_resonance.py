"""Addition two body resonance

Revision ID: 6f1cc0cea415
Revises: 2802742e9993
Create Date: 2016-05-17 14:26:38.395484

"""

# revision identifiers, used by Alembic.
revision = '6f1cc0cea415'
down_revision = '2802742e9993'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'two_body_resonance',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('first_body_id', sa.Integer, sa.ForeignKey('planet.id'), nullable=False),
        sa.Column('small_body_id', sa.Integer, sa.ForeignKey('asteroid.id'), nullable=False)
    )
    op.create_unique_constraint('uc_first_small', 'two_body_resonance',
                                ['first_body_id', 'small_body_id'])


def downgrade():
    op.drop_table('two_body_resonance')
