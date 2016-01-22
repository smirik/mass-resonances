from abc import abstractmethod
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
                 orbital_elem_set: IOrbitalElementSetFacade):
        self._orbital_elem_set = orbital_elem_set
        self._resonance = libration_resonance

    def build(self) -> Libration:
        finder = self._get_finder()
        years = finder.get_years()
        return Libration(self._resonance, years, X_STOP, self.is_apocetric())

    @abstractmethod
    def _get_finder(self) -> CirculationYearsFinder:
        pass

    @abstractmethod
    def is_apocetric(self) -> bool:
        pass


class TransientBuilder(_AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        transient_finder = CirculationYearsFinder(self._resonance.id, self.is_apocetric())
        return transient_finder

    def is_apocetric(self) -> bool:
        return False


class ApocentricBuilder(_AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        apocentric_finder = CirculationYearsFinder(self._resonance.id, self.is_apocetric())
        return apocentric_finder

    def is_apocetric(self) -> bool:
        return True


class LibrationDirector:
    def build(self, builder: _AbstractLibrationBuilder):
        libration = builder.build()
        return libration
