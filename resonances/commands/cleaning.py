import logging
import os
from typing import Tuple

from resonances.datamining import get_file_name
from resonances.datamining import get_resonances
from resonances.entities import Phase
from redis.exceptions import ConnectionError

from resonances.entities.dbutills import engine, REDIS

TABLENAME = Phase.__tablename__


def _log_redis(is_logged):
    if not is_logged:
        logging.info('Can\'t connect to Redis. Resonance phases could be remain in Redis.')
    return True


def clear_phases(start: int, stop: int, planets: Tuple[str]):
    conn = engine.connect()
    resonance_ids = []
    redis_logged = False
    for resonance in get_resonances(start, stop, False, planets):
        try:
            REDIS.delete('%s:%i' % (TABLENAME, resonance.id))
        except ConnectionError:
            redis_logged = _log_redis(redis_logged)

        resonance_ids.append(str(resonance.id))

        filename = get_file_name(resonance.id)
        if os.path.exists(filename):
            os.remove(filename)

    conn.execute("DELETE FROM %s WHERE resonance_id = ANY('{%s}'::int[]);" %
                 (TABLENAME, ','.join(resonance_ids)))
