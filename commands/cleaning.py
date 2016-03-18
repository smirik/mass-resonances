import os

from datamining import get_resonances
from datamining import get_file_name
from entities import Phase
from entities.dbutills import engine, REDIS

TABLENAME = Phase.__tablename__


def clear_phases(start: int, stop: int):
    conn = engine.connect()
    resonance_ids = []
    for resonance in get_resonances(start, stop):
        REDIS.delete('%s:%i' % (TABLENAME, resonance.id))
        resonance_ids.append(str(resonance.id))

        filename = get_file_name(resonance.id)
        if os.path.exists(filename):
            os.remove(filename)

    conn.execute("DELETE FROM %s WHERE resonance_id = ANY('{%s}'::int[]);" %
                 (TABLENAME, ','.join(resonance_ids)))
