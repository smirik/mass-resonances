from os import mkdir, getcwd
from typing import Tuple, List

from datamining import PhaseBuilder, PhaseStorage, build_bigbody_elements, \
    ResonanceOrbitalElementSetFacade, PhaseLoader
from datamining.orbitalelements import FilepathBuilder
from datamining.resonances import AEIDataGetter
from os.path import join as opjoin
from os.path import basename
from os.path import exists
from entities.body import Asteroid, Planet
from entities.dbutills import session
from entities import ThreeBodyResonance
from entities import TwoBodyResonance
from settings import Config
from boto.s3.connection import S3Connection
from sqlalchemy.orm import aliased
from .plot import ResfileMaker

CONFIG = Config.get_params()
BUCKET = CONFIG['s3']['bucket']
PROJECT_DIR = Config.get_project_dir()


def is_s3(path) -> bool:
    return 's3://' == path[:5]


def get_from_s3(filepaths: List[str]) -> List[str]:
    new_paths = []
    if any([is_s3(x) for x in filepaths]):
        conn = S3Connection(CONFIG['s3']['access_key'], CONFIG['s3']['secret_key'])
        bucket = conn.get_bucket(BUCKET)
        for path in filepaths:
            if not is_s3(path):
                continue
            start = path.index(BUCKET)
            filename = path[start + len(BUCKET) + 1:]
            folder = opjoin(PROJECT_DIR, '.s3files')
            if not exists(folder):
                mkdir(folder)
            local_path = opjoin(folder, basename(filename))
            if not exists(local_path):
                s3key = bucket.get_key(filename, validate=False)
                with open(local_path, 'wb') as f:
                    s3key.get_contents_to_file(f)
            new_paths.append(local_path)
    return new_paths


def genres(asteroid_number: int, integers: Tuple, filepaths: List[str], planets: Tuple):
    t1 = aliased(Planet)
    t2 = aliased(Planet)
    cond = len(integers) == 3
    resonance_cls = ThreeBodyResonance if cond else TwoBodyResonance
    query = session.query(resonance_cls).outerjoin(t1, t1.id == resonance_cls.first_body_id) \
        .filter(t1.name == planets[0])
    if cond:
        query = query.outerjoin(t2, t2.id == resonance_cls.second_body_id) \
            .filter(t2.name == planets[1])
    query = query.outerjoin(Asteroid, Asteroid.id == resonance_cls.small_body_id) \
        .filter(Asteroid.name == 'A%i' % asteroid_number)

    resonance = query.first()
    resonance_id = resonance.id

    phase_storage = PhaseStorage.file
    phase_builder = PhaseBuilder(phase_storage)
    phase_loader = PhaseLoader(phase_storage)

    print('Loading aei files.')
    filepaths = get_from_s3(filepaths) + [x for x in filepaths if not is_s3(x)]
    builder = FilepathBuilder(filepaths, True)
    planet_aei_paths = [builder.build('%s.aei' % x) for x in planets]
    resmaker = ResfileMaker(planets, planet_aei_paths)
    getter = AEIDataGetter(builder)
    orbital_element_sets = build_bigbody_elements(planet_aei_paths)
    orbital_elem_set_facade = ResonanceOrbitalElementSetFacade(orbital_element_sets, resonance)

    aei_data = getter.get_aei_data(asteroid_number)
    phase_builder.build(aei_data, resonance_id, orbital_elem_set_facade)
    phases = phase_loader.load(resonance_id)

    folder = opjoin(getcwd(), 'res')
    if not exists(folder):
        mkdir(folder)
    resmaker.make(phases, aei_data, opjoin(
        folder, 'A%i_%s_%s.res' % (asteroid_number, planets, '_'.join([str(x) for x in integers]))
    ))
