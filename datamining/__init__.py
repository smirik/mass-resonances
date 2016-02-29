import json
from typing import Dict, List

from catalog import get_resonances
from entities import Phase
from .orbitalelements import OrbitalElementSetCollection
from .orbitalelements import ComputedOrbitalElementSetFacade
from .orbitalelements import ResonanceOrbitalElementSetFacade
from .orbitalelements import build_bigbody_elements
from .orbitalelements import IOrbitalElementSetFacade
from .orbitalelements import ElementCountException
from .orbitalelements import PhaseCountException
from .orbitalelements import OrbitalElementSet

from .librations import ApocentricBuilder
from .librations import TransientBuilder
from .librations import LibrationDirector

from entities.dbutills import REDIS
from entities.dbutills import session


def save_phases(serialized_phases: List[Dict[str, float]], for_resonance_id: int):
    objs = [
        Phase(resonance_id=for_resonance_id, year=x['year'], value=x['value'],
              is_for_apocentric=False)
        for x in serialized_phases
    ]
    session.bulk_save_objects(objs)


def migrate_phases(start_asteroid: int, stop_asteroid: int):
    tablename = Phase.__tablename__

    for resonance, aei_data in get_resonances(start_asteroid, stop_asteroid):
        resonance_id = resonance.id
        for x in REDIS.lrange('%s:%i' % (tablename, resonance_id), 0, -1):
            serialized_phases = json.loads(x.decode('utf-8').replace('\'', '"'))
            save_phases(serialized_phases, resonance_id)

        session.commit()
