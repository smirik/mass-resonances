"""add planet names table

Revision ID: c6b695987112
Revises: 1e859493e69e
Create Date: 2016-04-18 22:00:57.666539

"""

# revision identifiers, used by Alembic.
revision = 'c6b695987112'
down_revision = '1e859493e69e'
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.sql.expression import table
from sqlalchemy.sql.expression import column
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'planet_name',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
    )
    op.create_unique_constraint('uc_planet_name', 'planet_name', ['name'])
    op.add_column('libration', sa.Column(
        'first_planet_name_id', sa.Integer, sa.ForeignKey('planet_name.id'), nullable=True
    ))
    op.add_column('libration', sa.Column(
        'second_planet_name_id', sa.Integer, sa.ForeignKey('planet_name.id'), nullable=True
    ))

    planet_name_table = table('planet_name', column('id', sa.Integer), column('name', sa.String))
    op.bulk_insert(planet_name_table, [
        {'id': 9, 'name': 'PLUTO'},
        {'id': 8, 'name': 'NEPTUNE'},
        {'id': 7, 'name': 'URANUS'},
        {'id': 6, 'name': 'SATURN'},
        {'id': 5, 'name': 'JUPITER'},
        {'id': 4, 'name': 'MARS'},
        {'id': 3, 'name': 'EARTHMOO'},
        {'id': 2, 'name': 'VENUS'},
        {'id': 1, 'name': 'MERCURY'},
    ])

    op.execute('UPDATE libration SET first_planet_name_id=5, second_planet_name_id=6')


def downgrade():
    op.drop_column('libration', 'first_planet_name_id')
    op.drop_column('libration', 'second_planet_name_id')
    op.drop_table('planet_name')
