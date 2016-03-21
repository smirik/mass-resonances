import json
import logging
from typing import List, Dict

from datamining import get_aggregated_resonances, PhaseBuilder
from datamining.orbitalelements.collection import AEIValueError
from datamining import PhaseStorage, PhaseCleaner
from entities.body import BrokenAsteroid
from entities.dbutills import REDIS, get_or_create
from datamining import ResonanceOrbitalElementSetFacade
from datamining import build_bigbody_elements
from datamining import ApocentricBuilder
from datamining import TransientBuilder
from datamining import LibrationDirector
from entities import Libration, ThreeBodyResonance
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

    classifier = _LibrationClassifier(is_current)
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


class _NoTransientException(Exception):
    pass


def _save_as_transient(libration: Libration, resonance: ThreeBodyResonance, asteroid_num: int,
                       resonance_str: str):
    if not libration.is_pure:
        if libration.is_transient:
            if libration.percentage:
                logging.info('A%i, %s, resonance = %s', asteroid_num,
                             str(libration), str(resonance))
                return True
            else:
                logging.debug(
                    'A%i, NO RESONANCE, resonance = %s, max = %f',
                    asteroid_num, resonance_str, libration.max_diff
                )
                session.expunge(libration)
                raise _NoTransientException()
        raise _NoTransientException()
    return False


class _LibrationClassifier:
    """
    Class is need for determining type of libration. If it needs, class will build libration by
    resonances and orbital elements of related sky bodies.
    """
    def __init__(self, get_from_db):
        self._get_from_db = get_from_db
        self._libration_director = LibrationDirector()
        self._resonance = None  # type: ThreeBodyResonance
        self._resonance_str = None  # type: str
        self._asteroid_num = None   # type: int
        self._libration = None  # type: Libration

    def set_resonance(self, resonance: ThreeBodyResonance):
        """
        Wroks as hook before classifying libration. It is need for saving useful data before any
        actions on resonance's libration by SQLalchemy, because we can try get something from
        resonance, and doesn't allow us remove libration.
        :param resonance:
        """
        self._resonance = resonance
        self._resonance_str = str(resonance)
        self._asteroid_num = self._resonance.asteroid_number
        self._libration = self._resonance.libration

    def classify(self, orbital_elem_set: ResonanceOrbitalElementSetFacade,
                 serialized_phases: List[Dict[str, float]]) -> bool:
        """
        Determines class of libration. Libration can be loaded from database if object has upped
        flag _get_from_db. If libration's class was not determined, libration will be removed and
        method returns False else libration will be saved and method return True.
        :param serialized_phases:
        :param orbital_elem_set:
        :return: flag of successful determining class of libration.
        """
        if not self._get_from_db and self._libration is None:
            builder = TransientBuilder(self._resonance, orbital_elem_set, serialized_phases)
            self._libration = self._libration_director.build(builder)
        elif not self._libration:
            return True

        try:
            if _save_as_transient(self._libration, self._resonance, self._asteroid_num,
                                  self._resonance_str):
                return True
            elif not self._libration.is_apocentric:
                logging.info('A%i, pure resonance %s', self._asteroid_num, self._resonance_str)
                return True
            raise _NoTransientException()
        except _NoTransientException:
            if not self._get_from_db and not self._libration.is_apocentric:
                builder = ApocentricBuilder(self._resonance, orbital_elem_set, serialized_phases)
                self._libration = self._libration_director.build(builder)

            if self._libration.is_pure:
                logging.info('A%i, pure apocentric resonance %s', self._asteroid_num,
                             self._resonance_str)
                return True
            else:
                session.expunge(self._libration)
        return False


class _BrokenAsteroidMediator:
    def __init__(self, asteroid_name: str):
        self._asteroid_name = asteroid_name

    def check(self):
        return session.query(exists().where(BrokenAsteroid.name == self._asteroid_name)).scalar()

    def save(self):
        get_or_create(BrokenAsteroid, name=self._asteroid_name)

