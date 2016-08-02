import json
import logging

from typing import List, Dict, Tuple

import warnings
from datamining import get_aggregated_resonances, PhaseBuilder
from datamining import AEIDataGetter
from datamining import LibrationClassifier
from datamining.orbitalelements import FilepathBuilder
from datamining.orbitalelements.collection import AEIValueError
from datamining import PhaseStorage, PhaseCleaner
from entities import BodyNumberEnum
from entities.body import BrokenAsteroid
from entities.dbutills import REDIS, get_or_create, engine
from datamining import ResonanceOrbitalElementSetFacade
from datamining import build_bigbody_elements
from entities.dbutills import session
from os.path import join as opjoin
from settings import Config
from shortcuts import get_asteroid_interval, ProgressBar
from sqlalchemy import exists
from sqlalchemy.orm import exc

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
OUTPUT_ANGLE = CONFIG['output']['angle']
DEBUG = 10


class LibrationFilder:
    def __init__(self, planets: Tuple[str], is_recursive: bool, clear: bool,
                 clear_s3: bool, is_current: bool = False,
                 phase_storage: PhaseStorage = PhaseStorage.redis, is_verbose: bool = False):
        self._is_verbose = is_verbose
        self._clear_s3 = clear_s3
        self._planets = planets
        self._is_recursive = is_recursive
        self._is_current = is_current
        self._phase_storage = phase_storage
        self._clear = clear
        conn = engine.connect()
        conn.execute('SELECT setval(\'libration_id_seq\', '
                     'COALESCE((SELECT MAX(id)+1 FROM libration), 1), false);')

    def find(self, start: int, stop: int, aei_paths: tuple):
        """Analyze resonances for pointed half-interval of numbers of asteroids. It gets resonances
        aggregated to asteroids. Computes resonant phase by orbital elements from prepared aei files
        of three bodies (asteroid and two planets). After this it finds circulations in vector of
        resonant phases and solves, based in circulations, libration does exists or no.

        :param aei_paths:
        :param start: start point of half-interval.
        :param stop: stop point of half-interval. It will be excluded.
        :return:
        """
        orbital_element_sets = None
        pathbuilder = FilepathBuilder(aei_paths, self._is_recursive, self._clear_s3)
        filepaths = [pathbuilder.build('%s.aei' % x) for x in self._planets]
        try:
            orbital_element_sets = build_bigbody_elements(filepaths)
        except AEIValueError:
            logging.error('Incorrect data in %s' % ' or in '.join(filepaths))
            exit(-1)

        aei_getter = AEIDataGetter(pathbuilder, self._clear)
        classifier = LibrationClassifier(self._is_current, BodyNumberEnum(len(self._planets) + 1))
        phase_builder = PhaseBuilder(self._phase_storage)
        phase_cleaner = PhaseCleaner(self._phase_storage)

        p_bar = None
        if self._is_verbose:
            p_bar = ProgressBar((stop + 1 - start), 'Find librations')
        asteroid_name = None
        for resonance, aei_data in get_aggregated_resonances(start, stop, False, self._planets,
                                                             aei_getter):
            if self._is_verbose and asteroid_name != resonance.small_body.name:
                p_bar.update()
            asteroid_name = resonance.small_body.name
            broken_asteroid_mediator = _BrokenAsteroidMediator(asteroid_name)
            if broken_asteroid_mediator.check():
                continue

            logging.debug('Analyze asteroid %s, resonance %s' % (asteroid_name, resonance))
            resonance_id = resonance.id
            classifier.set_resonance(resonance)
            orbital_elem_set_facade = ResonanceOrbitalElementSetFacade(orbital_element_sets,
                                                                       resonance)
            try:
                serialized_phases = phase_builder.build(aei_data, resonance_id,
                                                        orbital_elem_set_facade)
            except AEIValueError:
                broken_asteroid_mediator.save()
                phase_cleaner.delete(resonance_id)
                continue
            classifier.classify(orbital_elem_set_facade, serialized_phases)
            if self._clear:
                phase_cleaner.delete(resonance_id)

        session.commit()

    def find_by_file(self, aei_paths: tuple):
        """Do same that find but asteroid interval will be determined by filenames.

        :param aei_paths:
        :return:
        """
        for path in aei_paths:
            start, stop = get_asteroid_interval(path)
            logging.info('find librations for asteroids [%i %i], from %s' % (start, stop, path))
            self.find(start, stop, (path,))


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
