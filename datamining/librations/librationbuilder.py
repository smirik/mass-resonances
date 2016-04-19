from typing import Dict, List

from abc import abstractmethod
from entities.body import PlanetName
from settings import Config
from .finder import CirculationYearsFinder
from entities import Libration
from datamining import IOrbitalElementSetFacade
from entities import ThreeBodyResonance

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
X_STOP = CONFIG['gnuplot']['x_stop']
OUTPUT_ANGLE = CONFIG['output']['angle']


class _AbstractLibrationBuilder:
    def __init__(self, libration_resonance: ThreeBodyResonance,
                 orbital_elem_set: IOrbitalElementSetFacade,
                 serialized_phases: List[Dict[str, float]]):
        self._serialized_phases = serialized_phases
        self._orbital_elem_set = orbital_elem_set
        self._resonance = libration_resonance

    def build(self, bodyname1: PlanetName, bodyname2: PlanetName) -> Libration:
        finder = self._get_finder()
        years = finder.get_time_breaks()
        return Libration(self._resonance, years, X_STOP, self.is_apocetric(), bodyname1, bodyname2)

    @abstractmethod
    def _get_finder(self) -> CirculationYearsFinder:
        pass

    @abstractmethod
    def is_apocetric(self) -> bool:
        pass


class TransientBuilder(_AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        transient_finder = CirculationYearsFinder(self._resonance.id, self.is_apocetric(),
                                                  self._serialized_phases)
        return transient_finder

    def is_apocetric(self) -> bool:
        return False


class ApocentricBuilder(_AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        apocentric_finder = CirculationYearsFinder(self._resonance.id, self.is_apocetric(),
                                                   self._serialized_phases)
        return apocentric_finder

    def is_apocetric(self) -> bool:
        return True


class LibrationDirector:
    def __init__(self, bodyname1: PlanetName, bodyname2: PlanetName):
        self._body2 = bodyname2
        self._body1 = bodyname1

    def build(self, builder: _AbstractLibrationBuilder) -> Libration:
        libration = builder.build(self._body1, self._body2)
        return libration
