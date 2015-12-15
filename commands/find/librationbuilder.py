from typing import Tuple
import logging

import os
from abc import abstractmethod
from integrator import ResonanceOrbitalElementSet
from os.path import join as opjoin
from settings import Config
from utils.series import CirculationYearsFinder
from entities import Libration
from integrator.calc import BigBodyOrbitalElementSet
from entities import ThreeBodyResonance

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
X_STOP = CONFIG['gnuplot']['x_stop']
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
OUTPUT_ANGLE = CONFIG['output']['angle']


def get_orbitalelements_filepaths(body_number: int) -> Tuple[str, str, str]:
    mercury_dir = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
    mercury_planet_dir = mercury_dir

    body_number_start = body_number - body_number % 100
    body_number_stop = body_number_start + BODIES_COUNTER
    aei_dir = opjoin(
        PROJECT_DIR, CONFIG['export']['aei_dir'],
        '%i-%i' % (body_number_start, body_number_stop), 'aei'
    )
    aei_filepath = opjoin(aei_dir, 'A%i.aei' % body_number)
    if os.path.exists(aei_filepath):
        mercury_dir = aei_dir
        mercury_planet_dir = opjoin(
            PROJECT_DIR, CONFIG['export']['aei_dir'], 'Planets'
        )

    smallbody_filepath = opjoin(mercury_dir, 'A%i.aei' % body_number)
    firstbody_filepath = opjoin(mercury_planet_dir, '%s.aei' % BODY1)
    secondbody_filepath = opjoin(mercury_planet_dir, '%s.aei' % BODY2)

    return smallbody_filepath, firstbody_filepath, secondbody_filepath


class AbstractLibrationBuilder:

    def __init__(self, asteroid_number: int, libration_resonance: ThreeBodyResonance,
                 firstbody_elems: BigBodyOrbitalElementSet,
                 secondbody_elems: BigBodyOrbitalElementSet, build_resfile: bool):
        self._build_resfile = build_resfile
        self._resonance = libration_resonance
        self._firstbody_elements = firstbody_elems
        self._secondbody_elements = secondbody_elems
        self._res_filepath = self._prepare_resfile(asteroid_number, self._resonance)

    def _prepare_resfile(self, for_asteroid_num: int,
                         by_resonance: ThreeBodyResonance) -> str:
        smallbody_path, firstbody_path, secondbody_path \
            = get_orbitalelements_filepaths(for_asteroid_num)
        res_filepath = opjoin(PROJECT_DIR, OUTPUT_ANGLE, 'A%i.res' % for_asteroid_num)
        logging.debug("Check asteroid %i", for_asteroid_num)
        if self._build_resfile:
            orbital_elem_set = ResonanceOrbitalElementSet(
                by_resonance, self._firstbody_elements, self._secondbody_elements
            )
            if not os.path.exists(os.path.dirname(res_filepath)):
                os.makedirs(os.path.dirname(res_filepath))

            with open(res_filepath, 'w+') as resonance_file:
                for item in orbital_elem_set.get_elements(smallbody_path):
                    resonance_file.write(item)

        return res_filepath

    def build(self) -> Libration:
        finder = self._get_finder()
        return Libration(self._resonance, finder.get_years(), X_STOP,
                         self.is_apocetric())

    @abstractmethod
    def _get_finder(self) -> CirculationYearsFinder:
        pass

    @abstractmethod
    def is_apocetric(self) -> bool:
        pass


class TransientBuilder(AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        transient_finder = CirculationYearsFinder(False, self._res_filepath)
        return transient_finder

    def is_apocetric(self) -> bool:
        return False


class ApocentricBuilder(AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        apocentric_finder = CirculationYearsFinder(True, self._res_filepath)
        return apocentric_finder

    def is_apocetric(self) -> bool:
        return True
