from typing import List

import pytest
from entities import TwoBodyResonance, TwoBodyLibration, Libration
from entities import ThreeBodyResonance
from entities.body import Planet, Asteroid
from entities.dbutills import engine
from sqlalchemy import Table

TARGET_TABLES = [x.__table__ for x in [  # type: List[Table]
    TwoBodyLibration,
    Libration,
    TwoBodyResonance,
    ThreeBodyResonance,
    Planet,
    Asteroid,
]]


def clear_resonance_finalizer(conn=None):
    if not conn:
        conn = engine.connect()

    for table in TARGET_TABLES:
        conn.execute(table.delete())


def get_class_path(cls: type) -> str:
    return '%s.%s' % (cls.__module__, cls.__name__)


@pytest.fixture()
def resonancesfixture(request):
    def tear_down():
        conn = engine.connect()
        conn.execute(TwoBodyResonance.__table__.delete())
        conn.execute(ThreeBodyResonance.__table__.delete())
        conn.execute(Planet.__table__.delete())
        conn.execute(Asteroid.__table__.delete())

    request.addfinalizer(tear_down)

