from resonances.entities.dbutills import OnConflictInsert
from resonances.entities.body import BrokenAsteroid
from resonances.entities.dbutills import engine
from sqlalchemy.sql import select
from sqlalchemy.sql import func
import pytest


@pytest.fixture
def fixture(request):
    def fin():
        conn = engine.connect()
        conn.execute(BrokenAsteroid.__table__.delete())

    request.addfinalizer(fin)


def test_on_conflict(fixture):
    table = BrokenAsteroid.__table__
    insert_q = table.insert().values(name='qwe')
    insert_q2 = table.insert().values(name='qwe')
    insert_q = OnConflictInsert(insert_q, ['name'])
    insert_q2 = OnConflictInsert(insert_q2, ['name'])

    conn = engine.connect()
    conn.execute(insert_q)
    conn.execute(insert_q2)

    sel = select([func.count()]).select_from(table).where(table.c.name == 'qwe')
    result = conn.execute(sel).scalar()
    assert result == 1
