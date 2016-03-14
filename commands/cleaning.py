from datamining.resonances import get_resonances
from entities import Phase
from entities.dbutills import engine, REDIS

TABLENAME = Phase.__tablename__


def clear_phases(start: int, stop: int):
    conn = engine.connect()
    for resonance in get_resonances(start, stop):
        conn.execute('DELETE FROM %s WHERE resonance_id=%i' % (TABLENAME, resonance.id))
        REDIS.delete('%s:%i' % (TABLENAME, resonance.id))
