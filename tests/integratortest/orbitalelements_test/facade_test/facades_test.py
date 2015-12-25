from typing import List
from unittest import mock

import pytest
from abc import abstractmethod
from entities import ThreeBodyResonance
from integrator import ComputedOrbitalElementSetFacade, IOrbitalElementSetFacade, \
    ResonanceOrbitalElementSetFacade
from integrator import ElementCountException
from integrator import PhaseCountException
from .shortcuts import first_aei_data, get_class_path
from .shortcuts import build_orbital_collection, build_elem_set


class _IFacadeBuilder:
    def __init__(self, phases: List[float] = None, resonances: List = None):
        self._resonances = resonances
        self._phases = phases

    @property
    def phases(self) -> List[float]:
        return self._phases if self._phases else [
            x.compute_resonant_phase() for x in self._resonances]

    @abstractmethod
    def build(self, second_bigbody_elems, first_bigbody_elems):
        pass


class _ComputedFacadeBuilder(_IFacadeBuilder):
    def build(self, second_bigbody_elems, first_bigbody_elems) \
            -> ComputedOrbitalElementSetFacade:
        assert self._phases is not None
        return ComputedOrbitalElementSetFacade(
            second_bigbody_elems, first_bigbody_elems, self._phases)


class _ResonanceFacadeBuilder(_IFacadeBuilder):
    def build(self, second_bigbody_elems, first_bigbody_elems) \
            -> ComputedOrbitalElementSetFacade:
        assert self._resonances is not None
        return ResonanceOrbitalElementSetFacade(
            second_bigbody_elems, first_bigbody_elems, self._resonances[0])


class _FacadeDirector:
    def __init__(self, second_bigbody_elems, first_bigbody_elems):
        self._first_bigbody_elems = first_bigbody_elems
        self._second_bigbody_elems = second_bigbody_elems

    def build(self, builder: _IFacadeBuilder) -> IOrbitalElementSetFacade:
        return builder.build(self._second_bigbody_elems,
                             self._first_bigbody_elems)


@pytest.fixture()
def _build_resonance(phase: float = None):
    with mock.patch(get_class_path(ThreeBodyResonance)) as mock_ThreeBodyResonance:
        obj = mock_ThreeBodyResonance()
        if phase is not None:
            obj.compute_resonant_phase.return_value = phase
        return obj


@pytest.mark.parametrize('side_effect, exception_cls, builder', [
    ([[0], ['qwe', None]], ElementCountException,
     _ComputedFacadeBuilder(phases=[3., 6., 9.])),
    ([[0, 'asd'], ['qwe', None]], PhaseCountException,
     _ComputedFacadeBuilder(phases=[3., 6., 9.])),
    ([[0], ['qwe', None]], ElementCountException,
     _ResonanceFacadeBuilder(resonances=[_build_resonance()])),
])
def test_init(side_effect, exception_cls, builder):
    first_bigbody_elems, second_bigbody_elems = build_orbital_collection(side_effect)
    director = _FacadeDirector(second_bigbody_elems, first_bigbody_elems)
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
    first_elems, second_elems = build_orbital_collection([
        [build_elem_set(first_serialized_planet)],
        [build_elem_set(second_serialized_planet)]
    ])
    director = _FacadeDirector(second_elems, first_elems)
    facade = director.build(builder)
    i = 0
    data = 'some expected header content'.split() + [aei_data]

    for linedata in facade.get_elements(data):
        assert linedata == (
            '0.000000 %f 2.765030 0.077237 0.174533 1.396263 2.690092 %s %s\n' %
            (builder.phases[i], first_serialized_planet, second_serialized_planet)
        )
        i += 1

    assert i > 0
