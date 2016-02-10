"""add epoch, link resonance to epoch

Revision ID: 4591d7852fb
Revises: 17f29fcd7ea
Create Date: 2016-02-10 18:16:07.375230

"""

# revision identifiers, used by Alembic.
revision = '4591d7852fb'
down_revision = '17f29fcd7ea'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'epoch',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('start_day', sa.Float),
        sa.Column('end_day', sa.Float)
    )

    op.add_column('resonance', sa.Column(
        'epoch_id', sa.Integer, sa.ForeignKey('epoch.id'), nullable=False
    ))


def downgrade():
    op.drop_table('epoch')
    op.drop_column('resonance', 'epoch_id')
