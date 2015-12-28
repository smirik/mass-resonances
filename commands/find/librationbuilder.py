from typing import Tuple, List, Iterable
import math

from abc import abstractmethod
from entities.dbutills import session
from entities.phase import Phase
from settings import Config
from utils.series import CirculationYearsFinder
from entities import Libration
from integrator import IOrbitalElementSetFacade
from entities import ThreeBodyResonance
from utils.shortcuts import cutoff_angle

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
X_STOP = CONFIG['gnuplot']['x_stop']
OUTPUT_ANGLE = CONFIG['output']['angle']


class _PhaseBuilder:
    def __init__(self, from_filepath: str, for_apocentric: bool,
                 for_resonance: ThreeBodyResonance):
        self._from_filepath = from_filepath
        self._for_apocentric = for_apocentric
        self._for_resonance = for_resonance
        self._resfile_line_data = []

    def build(self):
        for year, resonant_phase in self._get_line_data():
            yield Phase(
                year=year, value=resonant_phase,
                resonance_id=self._for_resonance.id,
                is_for_apocentric=self._for_apocentric
            )

    def _get_line_data(self) -> Iterable[Tuple[float, float]]:
        """
        :rtype : Generator[List[float], None, None]
        """
        def _get_data(from_array: List[float]) -> Tuple[float, float]:
            year = from_array[0]
            resonant_phase = from_array[1]
            if self._for_apocentric:
                resonant_phase = cutoff_angle(resonant_phase + math.pi)

            return year, resonant_phase

        if not self._resfile_line_data:
            with open(self._from_filepath) as file:
                for line in file:
                    data = [float(x) for x in line.split()]
                    self._resfile_line_data.append([data[0], data[1]])
                    yield _get_data(data)
        else:
            for item in self._resfile_line_data:
                yield _get_data(item)


class AbstractLibrationBuilder:
    def __init__(self, libration_resonance: ThreeBodyResonance,
                 orbital_elem_set: IOrbitalElementSetFacade,
                 res_filepath: str):
        self._orbital_elem_set = orbital_elem_set
        self._resonance = libration_resonance
        self._res_filepath = res_filepath

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

    def _get_phase_ids(self) -> List[int]:
        phases = []
        resonant_phase_builder = _PhaseBuilder(
            self._res_filepath, self.is_apocetric(), self._resonance)
        for i, resonant_phase in enumerate(resonant_phase_builder.build()):
            session.add(resonant_phase)
            phases.append(resonant_phase)
            if i % 1000 == 0:
                session.flush()
        session.flush()

        return [x.id for x in phases]


class TransientBuilder(AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        transient_finder = CirculationYearsFinder(self._get_phase_ids())
        return transient_finder

    def is_apocetric(self) -> bool:
        return False


class ApocentricBuilder(AbstractLibrationBuilder):
    def _get_finder(self) -> CirculationYearsFinder:
        apocentric_finder = CirculationYearsFinder(self._get_phase_ids())
        return apocentric_finder

    def is_apocetric(self) -> bool:
        return True


class LibrationDirector:
    def build(self, builder: AbstractLibrationBuilder):
        libration = builder.build()
        return libration
