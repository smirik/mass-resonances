from datamining.resonances import get_resonances
from entities import Phase
from entities.dbutills import engine, REDIS

TABLENAME = Phase.__tablename__


def clear_phases(start: int, stop: int):
    conn = engine.connect()
    resonance_ids = []
    for resonance in get_resonances(start, stop):
        REDIS.delete('%s:%i' % (TABLENAME, resonance.id))
        resonance_ids.append(str(resonance.id))

    conn.execute("DELETE FROM %s WHERE resonance_id = ANY('{%s}'::int[]);" %
                 (TABLENAME, ','.join(resonance_ids)))
