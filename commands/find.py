import logging
from typing import List, Dict

from catalog import find_resonances
from entities.dbutills import REDIS
from datamining import ResonanceOrbitalElementSetFacade
from datamining import build_bigbody_elements
from datamining import ApocentricBuilder
from datamining import TransientBuilder
from datamining import LibrationDirector
from datamining import save_phases
from entities import Phase, Libration, ThreeBodyResonance
from entities.dbutills import session
from os.path import join as opjoin
from settings import Config
from storage import ResonanceDatabase

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
OUTPUT_ANGLE = CONFIG['output']['angle']


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


class _LibrationClassifyier:
    """
    Class is need for determining type of libration. If it needs, class will build libration by
    resonances and orbital elements of related sky bodies.
    """
    def __init__(self, get_from_db):
        self._get_from_db = get_from_db
        self._libration_director = LibrationDirector()
        self._rdb = ResonanceDatabase(CONFIG['resonance']['db_file'])
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

    def classify(self, orbital_elem_set: ResonanceOrbitalElementSetFacade) -> bool:
        """
        Determines class of libration. Libration can be loaded from database if object has upped
        flag _get_from_db. If libration's class was not determined, libration will be removed and
        method returns False else libration will be saved and method return True.
        :param orbital_elem_set:
        :return: flag of successful determining class of libration.
        """
        if not self._get_from_db and self._libration is None:
            builder = TransientBuilder(self._resonance, orbital_elem_set)
            self._libration = self._libration_director.build(builder)
        elif not self._libration:
            return True

        try:
            if _save_as_transient(self._libration, self._resonance, self._asteroid_num,
                                  self._resonance_str):
                self._rdb.add_string(self._libration.as_transient())
                return True
            elif not self._libration.is_apocentric:
                logging.info('A%i, pure resonance %s', self._asteroid_num, self._resonance_str)
                self._rdb.add_string(self._libration.as_pure())
                return True
            raise _NoTransientException()
        except _NoTransientException:
            if not self._get_from_db and not self._libration.is_apocentric:
                builder = ApocentricBuilder(self._resonance, orbital_elem_set)
                self._libration = self._libration_director.build(builder)

            if self._libration.is_pure:
                self._rdb.add_string(self._libration.as_pure_apocentric())
                logging.info('A%i, pure apocentric resonance %s', self._asteroid_num,
                             self._resonance_str)
                return True
            else:
                session.expunge(self._libration)
        return False


def find(start: int, stop: int, is_current: bool = False, migrate_phases_to_db: bool = False):
    """Find all possible resonances for all asteroids from start to stop.

    :param start:
    :param stop:
    :param is_current:
    :param migrate_phases_to_db: needs for auto migration from redis to postgres
    :return:
    """

    firstbody_elements, secondbody_elements = build_bigbody_elements(
        opjoin(MERCURY_DIR, '%s.aei' % BODY1),
        opjoin(MERCURY_DIR, '%s.aei' % BODY2))

    finder = _LibrationClassifyier(is_current)

    for resonance, aei_data in find_resonances(start, stop):
        logging.debug('Analyze asteroid %s, resonance %s' % (resonance.small_body.name, resonance))
        resonance_id = resonance.id
        finder.set_resonance(resonance)

        orbital_elem_set = ResonanceOrbitalElementSetFacade(
            firstbody_elements, secondbody_elements, resonance)

        phases_rediskey = '%s:%i' % (Phase.__tablename__, resonance_id)
        serialized_phases = _build_redis_phases(aei_data, phases_rediskey, orbital_elem_set)

        if migrate_phases_to_db:
            save_phases(serialized_phases, resonance_id)
        finder.classify(orbital_elem_set)
        if migrate_phases_to_db and phases_rediskey:
            REDIS.delete(phases_rediskey)

    session.commit()
