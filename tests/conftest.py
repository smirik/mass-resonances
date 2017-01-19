import pytest
from resonances.entities import ThreeBodyResonance
from resonances.entities import TwoBodyResonance
from resonances.entities.dbutills import engine

from resonances.entities.body import Planet, Asteroid

@pytest.fixture()
def resonancesfixture(request):
    def tear_down():
        conn = engine.connect()
        conn.execute(TwoBodyResonance.__table__.delete())
        conn.execute(ThreeBodyResonance.__table__.delete())
        conn.execute(Planet.__table__.delete())
        conn.execute(Asteroid.__table__.delete())

    request.addfinalizer(tear_down)

