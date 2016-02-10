import logging
from typing import List

from catalog import find_resonances
from entities.dbutills import REDIS
from datamining import ResonanceOrbitalElementSetFacade
from datamining import build_bigbody_elements
from datamining import ApocentricBuilder
from datamining import TransientBuilder
from datamining import LibrationDirector
from entities import Phase, Libration, ThreeBodyResonance
from entities.dbutills import session
from entities.epoch import Epoch
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


def _build_redis_phases(by_aei_data: List[str], by_resonance: ThreeBodyResonance,
                        orbital_elem_set: ResonanceOrbitalElementSetFacade) -> List[str]:
    pipe = REDIS.pipeline()
    resonance_id = by_resonance.id
    keys = []
    for year, value in orbital_elem_set.get_resonant_phases(by_aei_data):
        key = '%s:%i' % (Phase.__tablename__, resonance_id)
        pipe = pipe.rpush(key, '%s' % dict(year=year, value=value))
        keys.append(key)
    pipe.execute()
    return keys


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


def find(start: int, stop: int, in_epoch: Epoch, is_current: bool = False):
    """Find all possible resonances for all asteroids from start to stop.

    :param in_epoch:
    :param is_current:
    :param stop:
    :param start:
    :return:
    """
    rdb = ResonanceDatabase(CONFIG['resonance']['db_file'])

    firstbody_elements, secondbody_elements = build_bigbody_elements(
        opjoin(MERCURY_DIR, '%s.aei' % BODY1),
        opjoin(MERCURY_DIR, '%s.aei' % BODY2))
    libration_director = LibrationDirector()

    for resonance, aei_data in find_resonances(start, stop, in_epoch):
        resonance_str = str(resonance)
        asteroid_num = resonance.asteroid_number
        libration = resonance.libration

        orbital_elem_set = ResonanceOrbitalElementSetFacade(
            firstbody_elements, secondbody_elements, resonance)
        _build_redis_phases(aei_data, resonance, orbital_elem_set)

        if not is_current and libration is None:
            builder = TransientBuilder(resonance, orbital_elem_set)
            libration = libration_director.build(builder)
        elif not libration:
            continue

        try:
            if _save_as_transient(libration, resonance, asteroid_num, resonance_str):
                rdb.add_string(libration.as_transient())
                continue
            elif not libration.is_apocentric:
                logging.info('A%i, pure resonance %s', asteroid_num, resonance_str)
                rdb.add_string(libration.as_pure())
                continue
            raise _NoTransientException()
        except _NoTransientException:
            if not is_current and not libration.is_apocentric:
                builder = ApocentricBuilder(resonance, orbital_elem_set)
                libration = libration_director.build(builder)

            if libration.is_pure:
                rdb.add_string(libration.as_pure_apocentric())
                logging.info('A%i, pure apocentric resonance %s', asteroid_num,
                             resonance_str)
            else:
                session.expunge(libration)
    session.commit()
