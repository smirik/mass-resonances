import os
from math import pi

from datamining import PhaseLoader, PhaseStorage
from os.path import join as opjoin
from typing import List

from datamining import get_aggregated_resonances
from datamining import ComputedOrbitalElementSetFacade
from datamining import build_bigbody_elements
from settings import Config
from shortcuts import cutoff_angle
from view import make_plot

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
OUTPUT_RES_PATH = opjoin(PROJECT_DIR, CONFIG['output']['angle'])
OUTPUT_IMAGES = opjoin(PROJECT_DIR, CONFIG['output']['images'])
OUTPUT_GNU_PATH = opjoin(PROJECT_DIR, CONFIG['output']['gnuplot'])


def plot(start: int, stop: int, phase_storage: PhaseStorage, for_librations: bool):
    resmaker = _ResfileMaker()

    if not os.path.exists(OUTPUT_IMAGES):
        os.makedirs(OUTPUT_IMAGES)

    if not os.path.exists(OUTPUT_GNU_PATH):
        os.makedirs(OUTPUT_GNU_PATH)

    phase_loader = PhaseLoader(phase_storage)
    for resonance, aei_data in get_aggregated_resonances(start, stop, for_librations):
        phases = phase_loader.load(resonance.id)
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
