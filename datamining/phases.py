import json
import os
from typing import Dict, List

from datamining import ResonanceOrbitalElementSetFacade
from entities.dbutills import REDIS, engine
from entities.dbutills import session
from entities import Phase
from enum import Enum
from enum import unique
from settings import Config

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
PHASE_DIR = CONFIG['phases_dir']

TABLENAME = Phase.__tablename__


@unique
class PhaseStorage(Enum):
    redis = 0
    db = 1
    file = 2


class PhaseCleaner:
    def __init__(self, phase_storage: PhaseStorage):
        self._phase_storage = phase_storage

    def delete(self, for_resonance_id):
        if self._phase_storage == PhaseStorage.redis:
            REDIS.delete(_get_rediskey_name(for_resonance_id))
        elif self._phase_storage == PhaseStorage.db:
            conn = engine.connect()
            conn.execute("DELETE FROM %s WHERE resonance_id = %s;" % (TABLENAME, for_resonance_id))
        elif self._phase_storage == PhaseStorage.file:
            filepath = get_file_name(for_resonance_id)
            if os.path.exists(filepath):
                os.remove(filepath)


class PhaseLoader:
    def __init__(self, phase_storage: PhaseStorage):
        self._phase_storage = phase_storage

    def load(self, resonance_id: int) -> List[float]:
        phases = None
        if self._phase_storage == PhaseStorage.redis:
            phases = [
                json.loads(x.decode('utf-8').replace('\'', '"'))['value']
                for x in REDIS.lrange(_get_rediskey_name(resonance_id), 0, -1)
            ]
        elif self._phase_storage == PhaseStorage.db:
            conn = engine.connect()
            result = conn.execute('SELECT value FROM %s WHERE resonance_id=%i' %
                                  (TABLENAME, resonance_id))
            phases = [x['value'] for x in result]
        elif self._phase_storage == PhaseStorage.file:
            with open(get_file_name(resonance_id)) as f:
                phases = [json.loads(x.replace('\'', '"'))['value'] for x in f]
        return phases


class PhaseBuilder:
    def __init__(self, phase_storage: PhaseStorage):
        self._phase_storage = phase_storage

    def build(self, by_aei_data: List[str], resonance_id: int,
              orbital_elem_set: ResonanceOrbitalElementSetFacade) \
            -> List[Dict[str, float]]:

        serialized_phases = [dict(year=year, value=value) for year, value in
                             orbital_elem_set.get_resonant_phases(by_aei_data)]
        if self._phase_storage == PhaseStorage.redis:
            _save_redis(serialized_phases, _get_rediskey_name(resonance_id))
        elif self._phase_storage == PhaseStorage.db:
            _save_db(serialized_phases, resonance_id)
        elif self._phase_storage == PhaseStorage.file:
            _save_file(serialized_phases, get_file_name(resonance_id))

        return serialized_phases


def get_file_name(for_resonance_id: int) -> str:
    return os.path.join(PROJECT_DIR, PHASE_DIR, '%s:%i.rphs' % (TABLENAME, for_resonance_id))


def _get_rediskey_name(for_resonance_id: int) -> str:
    return '%s:%i' % (TABLENAME, for_resonance_id)


def _save_redis(serialized_phases: List[Dict[str, float]], in_key: str):
    pipe = REDIS.pipeline()
    for phase in serialized_phases:
        pipe = pipe.rpush(in_key, '%s' % phase)
    pipe.execute()


def _save_db(serialized_phases: List[Dict[str, float]], for_resonance_id: int):
    objs = [
        Phase(resonance_id=for_resonance_id, year=x['year'], value=x['value'],
              is_for_apocentric=False)
        for x in serialized_phases
    ]
    session.bulk_save_objects(objs)


def _save_file(serialized_phases: List[Dict[str, float]], filename: str):
    if not os.path.exists(os.path.dirname(filename)):
        os.mkdir(os.path.dirname(filename))
    with open(filename, 'w') as f:
        for i, phase in enumerate(serialized_phases):
            if i > 0:
                f.write('\n')
            f.write(str(phase))
