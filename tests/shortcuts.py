import pytest
from entities import ThreeBodyResonance
from entities.body import Planet, Asteroid
from entities.dbutills import engine


def get_class_path(cls: type) -> str:
    return '%s.%s' % (cls.__module__, cls.__name__)


@pytest.fixture()
def resonancesfixture(request):
    def tear_down():
        conn = engine.connect()
        conn.execute(ThreeBodyResonance.__table__.delete())
        conn.execute(Planet.__table__.delete())
        conn.execute(Asteroid.__table__.delete())

    request.addfinalizer(tear_down)
