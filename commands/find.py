import json
import logging
from typing import List, Dict

from datamining import get_aggregated_resonances, PhaseBuilder
from datamining import LibrationClassifier
from datamining.orbitalelements.collection import AEIValueError
from datamining import PhaseStorage, PhaseCleaner
from entities.body import BrokenAsteroid
from entities.dbutills import REDIS, get_or_create
from datamining import ResonanceOrbitalElementSetFacade
from datamining import build_bigbody_elements
from entities.dbutills import session
from os.path import join as opjoin
from settings import Config
from sqlalchemy import exists

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
OUTPUT_ANGLE = CONFIG['output']['angle']


def find(start: int, stop: int, is_current: bool = False,
         phase_storage: PhaseStorage = PhaseStorage.redis):
    """Analyze resonances for pointed half-interval of numbers of asteroids. It gets resonances
    aggregated to asteroids. Computes resonant phase by orbital elements from prepared aei files of
    three bodies (asteroid and two planets). After this it finds circulations in vector of resonant
    phases and solves, based in circulations, libration does exists or no.

    :param phase_storage: needs for auto migration from redis to postgres
    :param start: start point of half-interval.
    :param stop: stop point of half-interval. It will be excluded.
    :param is_current:
    :return:
    """
    firstbody_elements, secondbody_elements = None, None
    firstbody_aei = opjoin(MERCURY_DIR, '%s.aei' % BODY1)
    secondbody_aei = opjoin(MERCURY_DIR, '%s.aei' % BODY2)
    try:
        firstbody_elements, secondbody_elements = build_bigbody_elements(
            firstbody_aei, secondbody_aei)
    except AEIValueError:
        logging.error('Incorrect data in %s or in %s' % (firstbody_aei, secondbody_aei))
        exit(-1)

    classifier = LibrationClassifier(is_current)
    phase_builder = PhaseBuilder(phase_storage)
    phase_cleaner = PhaseCleaner(phase_storage)

    for resonance, aei_data in get_aggregated_resonances(start, stop, False):
        broken_asteroid_mediator = _BrokenAsteroidMediator(resonance.small_body.name)
        if broken_asteroid_mediator.check():
            continue

        logging.debug('Analyze asteroid %s, resonance %s' % (resonance.small_body.name, resonance))
        resonance_id = resonance.id
        classifier.set_resonance(resonance)

        orbital_elem_set = ResonanceOrbitalElementSetFacade(
            firstbody_elements, secondbody_elements, resonance)

        try:
            serialized_phases = phase_builder.build(aei_data, resonance_id, orbital_elem_set)
        except AEIValueError:
            broken_asteroid_mediator.save()
            phase_cleaner.delete(resonance_id)
            continue
        classifier.classify(orbital_elem_set, serialized_phases)

    session.commit()


def _build_redis_phases(by_aei_data: List[str], in_key: str,
                        orbital_elem_set: ResonanceOrbitalElementSetFacade) \
        -> List[Dict[str, float]]:
    pipe = REDIS.pipeline()
    serialized_phases = []
    for year, value in orbital_elem_set.get_resonant_phases(by_aei_data):
        serialized_phase = dict(year=year, value=value)
        pipe = pipe.rpush(in_key, '%s' % serialized_phase)
        serialized_phases.append(serialized_phase)
    pipe.execute()
    return serialized_phases


def _save_resonances_tofile(by_aei_data: List[str], in_file: str,
                            orbital_elem_set: ResonanceOrbitalElementSetFacade) \
        -> List[Dict[str, float]]:
    serialized_phases = []
    with open(in_file, 'w') as f:
        for year, value in orbital_elem_set.get_resonant_phases(by_aei_data):
            serialized_phase = dict(year=year, value=value)
            f.write(str(serialized_phase))
            f.write('\n')
            serialized_phases.append(serialized_phase)
    return serialized_phases


def _get_phases_fromfile(from_file):
    with open(from_file, 'r') as f:
        phases = [
            json.loads(x.replace('\'', '"'))['value']
            for x in f
        ]
    return phases


class _BrokenAsteroidMediator:
    def __init__(self, asteroid_name: str):
        self._asteroid_name = asteroid_name

    def check(self):
        return session.query(exists().where(BrokenAsteroid.name == self._asteroid_name)).scalar()

    def save(self):
        get_or_create(BrokenAsteroid, name=self._asteroid_name)
