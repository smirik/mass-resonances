from abc import abstractmethod
from typing import Dict, List, cast

from resonances.datamining import IOrbitalElementSetFacade

from resonances.entities import Libration
from resonances.entities import ResonanceMixin
from resonances.entities import BodyNumberEnum
from resonances.entities import TwoBodyLibration
from resonances.entities import TwoBodyResonance
from resonances.entities import LibrationMixin
from resonances.entities import ThreeBodyResonance
from resonances.settings import Config
from .finder import CirculationYearsFinder

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
X_STOP = CONFIG['gnuplot']['x_stop']
OUTPUT_ANGLE = CONFIG['output']['angle']


class _AbstractLibrationBuilder:
    def __init__(self, libration_resonance: ResonanceMixin,
                 orbital_elem_set: IOrbitalElementSetFacade,
                 serialized_phases: List[Dict[str, float]]):
        self._serialized_phases = serialized_phases
        self._orbital_elem_set = orbital_elem_set
        self._resonance = libration_resonance

    def build(self, body_count: BodyNumberEnum) -> LibrationMixin:
        finder = self._get_finder()
        years = finder.get_time_breaks()

        if body_count == BodyNumberEnum.two:
            return TwoBodyLibration(cast(TwoBodyResonance, self._resonance), years, X_STOP,
                                    self.is_apocetric())
        else:
            return Libration(cast(ThreeBodyResonance, self._resonance), years, X_STOP,
                             self.is_apocetric())

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
    def __init__(self, body_count: BodyNumberEnum):
        self._body_count = body_count

    def build(self, builder: _AbstractLibrationBuilder) -> LibrationMixin:
        libration = builder.build(self._body_count)
        return libration
