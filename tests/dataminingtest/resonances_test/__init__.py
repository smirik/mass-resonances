from typing import Tuple
from typing import List

import pytest
from resonances.datamining import get_resonances
from resonances.datamining import get_resonances_by_asteroids

from .conftest import fixture_base


@pytest.mark.parametrize('start, stop, fixture_indexes', [
    (1, 3, (0, 0)),
    (1, 78, (0, 0)),
    (1, 79, (0, 0, 2, 2)),
    (78, 4900000, (2, 2, 1, 1)),
    (211, 5 * (10 ** 5), (1, 1))
])
def test_asteroid_numbers(resonancesfixture, start: int, stop: int, fixture_indexes: Tuple[int]):
    asteroid_nums, planets = resonancesfixture
    counter = 0
    for resonance in get_resonances(start, stop, False, planets):
        assert resonance.asteroid_number == asteroid_nums[fixture_indexes[counter]]
        counter += 1
    assert counter == len(fixture_indexes)


def test_ordering(resonancesfixture):
    asteroid_nums, planets = resonancesfixture
    max_asteroid_num = 0
    for resonance in get_resonances(1, 10 ** 5, False, planets):
        assert resonance.asteroid_number >= max_asteroid_num


def test_planets(resonance_fixture_different_planets):
    asteroid_nums, planets = resonance_fixture_different_planets
    for resonance in get_resonances(1, 10 ** 5, False, planets):
        for body, planet in zip(resonance.get_big_bodies(), planets):
            assert body.name == planet


@pytest.mark.parametrize('only_librations, resonance_count', [
    (True, 1), (False, 6)
])
def test_only_librations(only_librations, resonance_count, resonance_fixture_different_librations):
    asteroid_nums, planets, libration = resonance_fixture_different_librations
    assert len([x for x in get_resonances(1, 10 ** 5, only_librations, planets)]) == resonance_count


def test_if_there_are_non_numerical_asteroids(resonancesfixture):
    ASTEROIDS_NUMBER_IN_RESONANCESFIXTURE = 6
    planets = ('JUPITER', 'SATURN')
    line_data_set = ['1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split()]
    fixture_base(('2004A111',), (planets,), line_data_set)
    assert len([x for x in get_resonances(1, 10 ** 5, False, planets)])\
            == ASTEROIDS_NUMBER_IN_RESONANCESFIXTURE


@pytest.mark.parametrize('integers, control_integers, control_count', [
    (['==1', '==1', '==1'], [1, 1, 1], 1),
    (['==1', '==2', '==2'], [1, 2, 2], 1),
    (['*', '*', '*'], [], 2),
])
def test_get_resonances_by_asteroids(resonancesfixture, integers: List[str],
                                     control_integers: List[int], control_count: int):
    asteroid_nums, planets = resonancesfixture
    resonances = get_resonances_by_asteroids(['A1'], False, integers, planets)
    count = 0
    for resonance in resonances:
        count += 1
        if control_integers:
            assert resonance.first_body.longitude_coeff == control_integers[0]
            assert resonance.second_body.longitude_coeff == control_integers[1]
            assert resonance.small_body.longitude_coeff == control_integers[2]
    assert count == control_count
