from typing import Tuple, List
import pytest
from entities.body import Asteroid
from entities.dbutills import session, engine
from entities import ThreeBodyResonance, TwoBodyResonance, get_resonance_factory, \
    build_resonance, Libration, TwoBodyLibration
from datamining import get_resonances
from tests.shortcuts import clear_resonance_finalizer


@pytest.fixture()
def _resonancesfixture(request):
    asteroid_nums = 1, 211, 78
    planets = ('JUPITER', 'SATURN'),
    line_data_set = ['1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split()]
    _fixture_base(asteroid_nums, planets, line_data_set)
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
def _resonance_fixture_different_planets(request):
    asteroid_nums = 1, 211, 78
    unreachable_planets = request.param['unreachable_planets']
    planets = request.param['planets'], unreachable_planets
    line_data_set = request.param['line_data_set']
    _fixture_base(asteroid_nums, planets, line_data_set)
    request.addfinalizer(clear_resonance_finalizer)
    return asteroid_nums, planets[0]


@pytest.fixture(params=[
    {'planets': ('JUPITER', 'SATURN'),
     'line_data_set': ['1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split()]},
    {'planets': ('JUPITER',),
     'line_data_set': ['1 1 0 -3 4.1509'.split(), '1 2 0 -5 3.5083'.split()]},
])
def _resonance_fixture_different_librations(request):
    asteroid_nums = 1, 211, 78
    planets = request.param['planets']
    line_data_set = request.param['line_data_set']
    _fixture_base(asteroid_nums, (planets,), line_data_set)
    request.addfinalizer(clear_resonance_finalizer)

    cls = ThreeBodyResonance if len(planets) == 2 else TwoBodyResonance
    libration_cls = Libration if len(planets) == 2 else TwoBodyLibration
    resonance = session.query(cls).outerjoin(Asteroid).filter(
        Asteroid.number == asteroid_nums[0]).first()
    libration = libration_cls(resonance, [], 0, False)
    session.commit()
    return asteroid_nums, planets, libration


def _fixture_base(asteroid_nums: Tuple, planets: Tuple[Tuple], line_data_set: List[List]):
    for line_data in line_data_set:
        for num in asteroid_nums:
            for target_planets in planets:
                resonance_factory = get_resonance_factory(target_planets, line_data, num)
                build_resonance(resonance_factory)


@pytest.mark.parametrize('start, stop, fixture_indexes', [
    (1, 3, (0, 0)),
    (1, 78, (0, 0)),
    (1, 79, (0, 0, 2, 2)),
    (78, 4900000, (2, 2, 1, 1)),
    (211, 5 * (10 ** 5), (1, 1))
])
def test_asteroid_numbers(_resonancesfixture, start: int, stop: int, fixture_indexes: Tuple[int]):
    asteroid_nums, planets = _resonancesfixture
    counter = 0
    for resonance in get_resonances(start, stop, False, planets):
        assert resonance.asteroid_number == asteroid_nums[fixture_indexes[counter]]
        counter += 1
    assert counter == len(fixture_indexes)


def test_ordering(_resonancesfixture):
    asteroid_nums, planets = _resonancesfixture
    max_asteroid_num = 0
    for resonance in get_resonances(1, 10 ** 5, False, planets):
        assert resonance.asteroid_number >= max_asteroid_num


def test_planets(_resonance_fixture_different_planets):
    asteroid_nums, planets = _resonance_fixture_different_planets
    for resonance in get_resonances(1, 10 ** 5, False, planets):
        for body, planet in zip(resonance.get_big_bodies(), planets):
            assert body.name == planet


@pytest.mark.parametrize('only_librations, resonance_count', [
    (True, 1), (False, 6)
])
def test_only_librations(only_librations, resonance_count, _resonance_fixture_different_librations):
    asteroid_nums, planets, libration = _resonance_fixture_different_librations
    assert len([x for x in get_resonances(1, 10 ** 5, only_librations, planets)]) == resonance_count
