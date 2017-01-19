import pytest
from typing import Tuple, List

from resonances.entities import ThreeBodyResonance, TwoBodyResonance, get_resonance_factory, \
    build_resonance, Libration, TwoBodyLibration
from resonances.entities.dbutills import session
from resonances.entities.body import Asteroid
from tests.shortcuts import clear_resonance_finalizer


def fixture_base(asteroid_nums: Tuple, planets: Tuple[Tuple], line_data_set: List[List]):
    for line_data in line_data_set:
        for num in asteroid_nums:
            for target_planets in planets:
                resonance_factory = get_resonance_factory(target_planets, line_data, num)
                build_resonance(resonance_factory)


@pytest.fixture()
def resonancesfixture(request):
    asteroid_nums = 1, 211, 78
    planets = ('JUPITER', 'SATURN'),
    line_data_set = ['1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split()]
    fixture_base(asteroid_nums, planets, line_data_set)
    request.addfinalizer(clear_resonance_finalizer)
    return asteroid_nums, planets[0]


@pytest.fixture(params=[
    {'planets': ('JUPITER', 'SATURN'), 'unreachable_planets': ('VENUS', 'MARS'),
     'line_data_set': ['1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split()]},
    {'planets': ('MARS', 'JUPITER'), 'unreachable_planets': ('VENUS', 'MARS'),
     'line_data_set': ['1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split()]},
    {'planets': ('JUPITER',), 'unreachable_planets': ('MARS',),
     'line_data_set': ['1 1 0 -3 4.1509'.split(), '1 2 0 -5 3.5083'.split()]},
    {'planets': ('MARS',), 'unreachable_planets': ('EARHTMOO',),
     'line_data_set': ['1 1 0 -3 4.1509'.split(), '1 2 0 -5 3.5083'.split()]},
])
def resonance_fixture_different_planets(request):
    asteroid_nums = 1, 211, 78
    unreachable_planets = request.param['unreachable_planets']
    planets = request.param['planets'], unreachable_planets
    line_data_set = request.param['line_data_set']
    fixture_base(asteroid_nums, planets, line_data_set)
    request.addfinalizer(clear_resonance_finalizer)
    return asteroid_nums, planets[0]


@pytest.fixture(params=[
    {'planets': ('JUPITER', 'SATURN'),
     'line_data_set': ['1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split()]},
    {'planets': ('JUPITER',),
     'line_data_set': ['1 1 0 -3 4.1509'.split(), '1 2 0 -5 3.5083'.split()]},
])
def resonance_fixture_different_librations(request):
    asteroid_nums = 1, 211, 78
    planets = request.param['planets']
    line_data_set = request.param['line_data_set']
    fixture_base(asteroid_nums, (planets,), line_data_set)
    request.addfinalizer(clear_resonance_finalizer)

    cls = ThreeBodyResonance if len(planets) == 2 else TwoBodyResonance
    libration_cls = Libration if len(planets) == 2 else TwoBodyLibration
    resonance = session.query(cls).outerjoin(Asteroid).filter(
        Asteroid.number == asteroid_nums[0]).first()
    libration = libration_cls(resonance, [], 0, False)
    session.commit()
    return asteroid_nums, planets, libration

