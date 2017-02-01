import json
import logging
from os.path import join as opjoin
from typing import List
from typing import Dict
from typing import Tuple
from typing import Iterable

from resonances.datamining import OrbitalElementSetCollection
from resonances.datamining import AEIDataGetter
from resonances.datamining import LibrationClassifier
from resonances.datamining import PhaseStorage
from resonances.datamining import ResonanceOrbitalElementSetFacade
from resonances.datamining import build_bigbody_elements
from resonances.datamining import get_aggregated_resonances
from resonances.datamining import ResonanceAeiData
from resonances.datamining import PhaseBuilder
from resonances.datamining.orbitalelements import FilepathBuilder
from resonances.datamining.orbitalelements.collection import AEIValueError
from resonances.datamining import AsteroidElementCountException
from resonances.entities import BodyNumberEnum, Libration, TwoBodyLibration
from resonances.entities.dbutills import REDIS, engine
from resonances.entities.dbutills import session
from resonances.shortcuts import get_asteroid_interval, ProgressBar, fix_id_sequence
from sqlalchemy import exists
from resonances.entities.dbutills import OnConflictInsert

from resonances.entities.body import BrokenAsteroid
from resonances.settings import Config

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
OUTPUT_ANGLE = CONFIG['output']['angle']


class LibrationFinder:
    def __init__(self, planets: Tuple[str], is_recursive: bool, clear: bool,
                 clear_s3: bool, is_current: bool = False,
                 phase_storage: PhaseStorage = PhaseStorage.redis, is_verbose: bool = False):
        self._is_verbose = is_verbose
        self._clear_s3 = clear_s3
        self._planets = planets
        self._is_recursive = is_recursive
        self._is_current = is_current
        self._phase_storage = None if clear else phase_storage
        self._clear = clear
        conn = engine.connect()
        table = Libration.__table__ if len(planets) == 2 else TwoBodyLibration.__table__
        fix_id_sequence(table, conn)

    @property
    def planets(self):
        return self._planets

    def _find(self, resonances_data: Iterable[ResonanceAeiData], length: int,
              orbital_element_sets: List[OrbitalElementSetCollection]):
        """
        :param resonances_data:
        :param length: used only for progress bar.
        :param orbital_element_sets:
        """
        classifier = LibrationClassifier(self._is_current, BodyNumberEnum(len(self._planets) + 1))
        phase_builder = PhaseBuilder(self._phase_storage)
        p_bar = None
        if self._is_verbose:
            p_bar = ProgressBar(length, 'Find librations')
        asteroid_name = None
        for resonance, aei_data in resonances_data:
            if self._is_verbose and asteroid_name != resonance.small_body.name:
                p_bar.update()
            asteroid_name = resonance.small_body.name
            broken_asteroid_mediator = _BrokenAsteroidMediator(asteroid_name)
            if broken_asteroid_mediator.check():
                continue

            if not aei_data:
                broken_asteroid_mediator.save('Has no data in aei file.')

            logging.debug('Analyze asteroid %s, resonance %s' % (asteroid_name, resonance))
            resonance_id = resonance.id
            classifier.set_resonance(resonance)
            orbital_elem_set_facade = ResonanceOrbitalElementSetFacade(
                orbital_element_sets, resonance)
            try:
                serialized_phases = phase_builder.build(
                    aei_data, resonance_id, orbital_elem_set_facade)
            except AEIValueError:
                broken_asteroid_mediator.save()
                continue
            except AsteroidElementCountException as e:
                broken_asteroid_mediator.save(str(e))
                continue

            classifier.classify(orbital_elem_set_facade, serialized_phases)

        session.flush()
        session.commit()

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
        pathbuilder = FilepathBuilder(aei_paths, self._is_recursive, self._clear_s3)
        filepaths = [pathbuilder.build('%s.aei' % x) for x in self._planets]
        orbital_element_sets = None
        try:
            orbital_element_sets = build_bigbody_elements(filepaths)
        except AEIValueError:
            logging.error('Incorrect data in %s' % ' or in '.join(filepaths))
            exit(-1)

        aei_getter = AEIDataGetter(pathbuilder, self._clear)
        resonances_data_gen = get_aggregated_resonances(
            start, stop, False, self._planets, aei_getter)
        self._find(resonances_data_gen, stop + 1 - start, orbital_element_sets)

    def find_by_resonances(self, resonances_data: Iterable[ResonanceAeiData], aei_paths: tuple):
        pathbuilder = FilepathBuilder(aei_paths, self._is_recursive, self._clear_s3)
        filepaths = [pathbuilder.build('%s.aei' % x) for x in self._planets]
        orbital_element_sets = None
        try:
            orbital_element_sets = build_bigbody_elements(filepaths)
        except AEIValueError:
            logging.error('Incorrect data in %s' % ' or in '.join(filepaths))
            exit(-1)
        self._find(resonances_data, 0, orbital_element_sets)

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
        with session.no_autoflush:
            query = exists().where(BrokenAsteroid.name == self._asteroid_name)
            return session.query(query).scalar()

    def save(self, reason: str = None):
        table = BrokenAsteroid.__table__
        insert_q = table.insert().values(name=self._asteroid_name, reason=reason)
        insert_q = OnConflictInsert(insert_q, ['name'])

        connection = engine.connect()
        trans = connection.begin()
        try:
            connection.execute(insert_q)
            trans.commit()
        except:
            trans.rollback()
            raise
