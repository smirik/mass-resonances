from resonances.entities import ThreeBodyResonance
from resonances.entities import TwoBodyResonance, TwoBodyLibration, Libration
from resonances.entities.dbutills import engine

from resonances.entities.body import Planet, Asteroid

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
