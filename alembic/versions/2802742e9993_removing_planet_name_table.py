"""removing planet name table

Revision ID: 2802742e9993
Revises: d31ecc2d0185
Create Date: 2016-04-22 23:13:10.273937

"""

# revision identifiers, used by Alembic.
revision = '2802742e9993'
down_revision = 'd31ecc2d0185'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table
from sqlalchemy.sql.expression import column


def upgrade():
    op.execute('DELETE FROM libration WHERE first_planet_name_id != 5 and second_planet_name_id != 6')
    op.drop_constraint('uc_resonance_planet_names', 'libration')
    op.create_unique_constraint('libration_resonance_id_key', 'libration', ['resonance_id'])
    op.drop_column('libration', 'first_planet_name_id')
    op.drop_column('libration', 'second_planet_name_id')
    op.drop_table('planet_name')


def downgrade():
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

    op.alter_column('libration', 'first_planet_name_id', nullable=False)
    op.alter_column('libration', 'second_planet_name_id', nullable=False)
    op.drop_constraint('libration_resonance_id_key', 'libration')
    op.create_unique_constraint('uc_resonance_planet_names', 'libration',
                                ['resonance_id', 'first_planet_name_id', 'second_planet_name_id'])
