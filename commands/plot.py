import json
import os
from math import pi

from os.path import join as opjoin
from typing import List

from datamining import get_aggregated_resonances
from datamining import ComputedOrbitalElementSetFacade
from datamining import build_bigbody_elements
from entities import Phase
from entities.dbutills import REDIS, engine
from settings import Config
from shortcuts import cutoff_angle
from view import make_plot

TABLENAME = Phase.__tablename__
CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
OUTPUT_RES_PATH = opjoin(PROJECT_DIR, CONFIG['output']['angle'])
OUTPUT_IMAGES = opjoin(PROJECT_DIR, CONFIG['output']['images'])
OUTPUT_GNU_PATH = opjoin(PROJECT_DIR, CONFIG['output']['gnuplot'])


def plot(start: int, stop: int, from_db: bool):
    resmaker = _ResfileMaker()

    if not os.path.exists(OUTPUT_IMAGES):
        os.makedirs(OUTPUT_IMAGES)

    if not os.path.exists(OUTPUT_GNU_PATH):
        os.makedirs(OUTPUT_GNU_PATH)

    for resonance, aei_data in get_aggregated_resonances(start, stop):
        phases = _get_phases(resonance.id, from_db)
        apocentric_phases = [cutoff_angle(x + pi) for x in phases]
        res_filepath = opjoin(OUTPUT_RES_PATH, 'A%i.res' % resonance.asteroid_number)
        gnu_filepath = opjoin(OUTPUT_GNU_PATH, 'A%i.gnu' % resonance.asteroid_number)

        resmaker.make(phases, aei_data, res_filepath)
        png_path = opjoin(PROJECT_DIR, OUTPUT_IMAGES, 'A%i-res%i%s.png' % (
            resonance.asteroid_number, resonance.id, ''))
        make_plot(res_filepath, gnu_filepath, png_path)

        resmaker.make(apocentric_phases, aei_data, res_filepath)
        png_path = opjoin(PROJECT_DIR, OUTPUT_IMAGES, 'A%i-res%i%s.png' % (
            resonance.asteroid_number, resonance.id, '-apocentric'))
        make_plot(res_filepath, gnu_filepath, png_path)


class _ResfileMaker:
    def __init__(self):
        self._firstbody_elements, self._secondbody_elements = build_bigbody_elements(
            opjoin(MERCURY_DIR, '%s.aei' % BODY1),
            opjoin(MERCURY_DIR, '%s.aei' % BODY2))

    def make(self, with_phases: List[float], by_aei_data: List[str], filepath: str):
        orbital_elem_set = ComputedOrbitalElementSetFacade(
            self._firstbody_elements, self._secondbody_elements, with_phases)
        orbital_elem_set.write_to_resfile(filepath, by_aei_data)


def _get_phases(resonance_id: int, from_db: bool) -> List[float]:
    if from_db:
        conn = engine.connect()
        result = conn.execute('SELECT value FROM %s WHERE resonance_id=%i' %
                              (TABLENAME, resonance_id))
        phases = [x['value'] for x in result]
    else:
        phases = [
            json.loads(x.decode('utf-8').replace('\'', '"'))['value']
            for x in REDIS.lrange('%s:%i' % (TABLENAME, resonance_id), 0, -1)
        ]
    return phases
