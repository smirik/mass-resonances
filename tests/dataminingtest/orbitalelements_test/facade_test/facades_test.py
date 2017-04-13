from abc import abstractmethod
from typing import List
from unittest import mock

import pytest
from resonances.datamining import ComputedOrbitalElementSetFacade, OrbitalElementSetCollection
from resonances.datamining import ElementCountException
from resonances.datamining import IOrbitalElementSetFacade
from resonances.datamining import PhaseCountException
from resonances.datamining import ResonanceOrbitalElementSetFacade
from resonances.datamining import AsteroidElementCountException

from resonances.entities import ThreeBodyResonance
from resonances.entities.body import Asteroid
from resonances.entities.body import Planet
from tests.shortcuts import get_class_path
from .shortcuts import build_orbital_collection
from .shortcuts import build_elem_set
from .shortcuts import build_orbital_collection_set
from .shortcuts import first_aei_data
from .shortcuts import second_aei_data
from .shortcuts import third_aei_data

TEST_HEADER = 'some expected header content'.split()


class _IFacadeBuilder:
    def __init__(self, phases: List[float] = None, resonances: List = None):
        self._resonances = resonances
        self._phases = phases

    @property
    def phases(self) -> List[float]:
        return self._phases if self._phases else [
            x.compute_resonant_phase() for x in self._resonances]

    @abstractmethod
    def build(self, planet_elems: List[OrbitalElementSetCollection]):
        pass


class _ComputedFacadeBuilder(_IFacadeBuilder):
    def build(self, planet_elems: List[OrbitalElementSetCollection])\
            -> ComputedOrbitalElementSetFacade:
        assert self._phases is not None
        return ComputedOrbitalElementSetFacade(planet_elems, self._phases)


class _ResonanceFacadeBuilder(_IFacadeBuilder):
    def build(self, planet_elems: List[OrbitalElementSetCollection])\
            -> ResonanceOrbitalElementSetFacade:
        assert self._resonances is not None
        return ResonanceOrbitalElementSetFacade(planet_elems, self._resonances[0])


class _FacadeDirector:
    def __init__(self, planets_elems:  List[OrbitalElementSetCollection]):
        self._planets_elems = planets_elems

    def build(self, builder: _IFacadeBuilder) -> IOrbitalElementSetFacade:
        return builder.build(self._planets_elems)


@pytest.fixture()
def _build_resonance(phase: float = None):
    with mock.patch(get_class_path(ThreeBodyResonance)) as mock_ThreeBodyResonance:
        obj = mock_ThreeBodyResonance()
        if phase is not None:
            obj.compute_resonant_phase.return_value = phase

        type(obj).get_big_bodies = mock.MagicMock(return_value=[
            _build_planet(4), _build_planet(-2)])
        type(obj).small_body = mock.PropertyMock(return_value=_build_asteroid(-1, 2))
        return obj


def _build_planet(long: int):
    with mock.patch(get_class_path(Planet)) as planet_cls:
        return _build_body(planet_cls, long)


def _build_asteroid(long, peri):
    with mock.patch(get_class_path(Asteroid)) as asteroid_cls:
        return _build_body(asteroid_cls, long, peri)


def _build_body(cls, long: int, peri: int = 0):
    body = cls()
    type(body).longitude_coeff = mock.PropertyMock(return_value=long)
    type(body).perihelion_longitude_coeff = mock.PropertyMock(return_value=peri)
    return body



@pytest.mark.parametrize('mock_side_effect, exception_cls, builder', [
    ([[0], ['first_any_str', None]], ElementCountException,
     _ComputedFacadeBuilder(phases=[3., 6., 9.])),
    ([[0, 'second_any_str'], ['first_any_str', None]], PhaseCountException,
     _ComputedFacadeBuilder(phases=[3., 6., 9.])),
    ([[0], ['first_any_str', None]], ElementCountException,
     _ResonanceFacadeBuilder(resonances=[_build_resonance()])),
])
def test_init(mock_side_effect, exception_cls, builder):
    planets_elems = build_orbital_collection(mock_side_effect)
    director = _FacadeDirector(planets_elems)
    with pytest.raises(exception_cls):
        director.build(builder)


@pytest.mark.parametrize(
    'aei_data, first_serialized_planet, second_serialized_planet, builder', [
        (first_aei_data(), '5.203 0.048', '9.578 0.054',
         _ComputedFacadeBuilder(phases=[3.])),
        (first_aei_data(), '4.003 1.048', '8.578 1.014',
         _ComputedFacadeBuilder(phases=[2.112])),
        (first_aei_data(), '5.203 0.048', '9.578 0.054',
         _ResonanceFacadeBuilder(resonances=[_build_resonance(3.)])),
        (first_aei_data(), '4.003 1.048', '8.578 1.014',
         _ResonanceFacadeBuilder(resonances=[_build_resonance(2.112)])),
    ]
)
def test_get_elements(aei_data, first_serialized_planet, second_serialized_planet,
                      builder: _IFacadeBuilder):
    planet_elems = build_orbital_collection([
        [build_elem_set(first_serialized_planet)],
        [build_elem_set(second_serialized_planet)]
    ])
    director = _FacadeDirector(planet_elems)
    facade = director.build(builder)
    i = 0
    import pandas as pd
    aei_data = pd.DataFrame([], columns=['Time (years)', 'a', 'e', 'i', 'node', 'long'])
    data = TEST_HEADER + [aei_data]

    for linedata in facade.get_elements(data):
        assert linedata == (
            '0.000000 %f 2.765030 0.077237 0.174533 1.396263 2.690092 %s %s\n' %
            (builder.phases[i], first_serialized_planet, second_serialized_planet)
        )
        i += 1

    assert i > 0


@pytest.mark.parametrize(
    'aei_data, first_serialized_planet, second_serialized_planet, phase_values', [
        ([first_aei_data(), second_aei_data(), third_aei_data()],
         ['5.203 0.048', '3.203 0.037', '7.913 0.049'],
         ['9.578 0.054', '8.511 0.044', '6.070 0.041'],
         [-1.1913877375688626, 1.3964129457677625, 1.6286880229625851]),
        ([first_aei_data(), second_aei_data()],
         ['4.003 1.048', '5.203 0.048'],
         ['3.203 0.037', '6.070 0.041'],
         [0.47542695525155043, 1.7120423314085897]),
        ([first_aei_data()],
         ['4.003 1.048', '4.003 1.048'],
         ['8.578 1.014', '8.578 1.014'],
         None),
    ]
)
def test_get_resonant_phases(aei_data, first_serialized_planet: List[str],
                             second_serialized_planet: List[str], phase_values: List[float]):
    """
    Tests correctness of phases computing. Number of phases is equal to number
    of strings in first_serialized_planet or second_serialized_planet. Also
    lengths of first_serialized_planet and second_serialized_planet must be same.
    """
    builder = _ResonanceFacadeBuilder(resonances=[_build_resonance()])

    first_planet_elems = [build_elem_set(x) for x in first_serialized_planet]
    second_planet_elems = [build_elem_set(x) for x in second_serialized_planet]
    planet_elems = build_orbital_collection_set([first_planet_elems, second_planet_elems])
    director = _FacadeDirector(planet_elems)
    facade = director.build(builder)    # type: ResonanceOrbitalElementSetFacade

    if len(aei_data) == len(first_serialized_planet):
        aei_data = TEST_HEADER + aei_data
        _test_phase_correctness(aei_data, facade, phase_values)
    else:
        aei_data = TEST_HEADER + aei_data
        _test_get_resonant_phases_raise(aei_data, facade)


def _test_phase_correctness(aei_data, facade: ResonanceOrbitalElementSetFacade, phase_values):
    i = 0
    for time, resonant_phase in facade.get_resonant_phases(aei_data):
        assert time == float(aei_data[i + len(TEST_HEADER)].split()[0])
        assert resonant_phase == phase_values[i]
        i += 1

    assert i > 0


def _test_get_resonant_phases_raise(aei_data, facade: ResonanceOrbitalElementSetFacade):
    with pytest.raises(AsteroidElementCountException):
        for item in facade.get_resonant_phases(aei_data):
            pass
