"""addition of a contraint for resonance

Revision ID: 1e859493e69e
Revises: 3ee8b9885846
Create Date: 2016-03-24 22:42:53.315932

"""

# revision identifiers, used by Alembic.
revision = '1e859493e69e'
down_revision = '3ee8b9885846'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_unique_constraint('uc_first_second_small', 'resonance',
                                ['first_body_id', 'second_body_id', 'small_body_id'])


def downgrade():
    op.drop_constraint('uc_first_second_small', 'resonance')
