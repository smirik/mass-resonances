from typing import List, Dict

import math
from unittest import mock

import pytest
from entities import ThreeBodyResonance, build_resonance
from entities.body import Asteroid
from entities.body import LONG
from entities.body import PERI
from entities.body import LONG_COEFF
from entities.body import PERI_COEFF
from entities.body import Planet
from entities.dbutills import session, engine
from shortcuts import cutoff_angle
from sqlalchemy import and_, delete
from sqlalchemy.orm import joinedload, aliased
from tests.shortcuts import resonancesfixture, get_class_path


@mock.patch(get_class_path(Planet))
@mock.patch(get_class_path(Planet))
@mock.patch(get_class_path(Asteroid))
@pytest.mark.parametrize(
    ['jupiter', 'saturn', 'asteroid', 'cutoffed_resonant_phase',
     'jupiter_coeffs', 'saturn_coeffs', 'asteroid_coeffs'],
    [
        (
            {LONG: 2.856034797, PERI: math.radians(70.12327)},
            {LONG: 3.339293952, PERI: math.radians(124.8056)},
            {LONG: 6.551616946, PERI: math.radians(103.9978)},
            -3.137910531830559,
            {LONG: 3, PERI: 0},
            {LONG: -1, PERI: 0},
            {LONG: -1, PERI: -1}
        ),
        (
            {LONG: 6.093856353, PERI: math.radians(15.66345)},
            {LONG: 6.836146629, PERI: math.radians(88.52425)},
            {LONG: 2.795411134, PERI: math.radians(21.54496)},
            -2.8669537513497794,
            {LONG: 7, PERI: 0},
            {LONG: -2, PERI: 0},
            {LONG: -2, PERI: -3}
        ),
    ]
)
def test_compute_resonant_phase(asteroid_mockcls, jupiter_mockcls, saturn_mockcls,
                                jupiter, saturn, asteroid, cutoffed_resonant_phase,
                                jupiter_coeffs, saturn_coeffs, asteroid_coeffs):
    asteroid_mock = asteroid_mockcls()
    asteroid_mock.longitude_coeff = asteroid_coeffs[LONG]
    asteroid_mock.perihelion_longitude_coeff = asteroid_coeffs[PERI]

    jupiter_mock = jupiter_mockcls()
    jupiter_mock.longitude_coeff = jupiter_coeffs[LONG]
    jupiter_mock.perihelion_longitude_coeff = jupiter_coeffs[PERI]

    saturn_mock = saturn_mockcls()
    saturn_mock.longitude_coeff = saturn_coeffs[LONG]
    saturn_mock.perihelion_longitude_coeff = saturn_coeffs[PERI]

    resonance = ThreeBodyResonance()
    resonance.first_body = jupiter_mock
    resonance.second_body = saturn_mock
    resonance.small_body = asteroid_mock

    resonant_phase = resonance.compute_resonant_phase(jupiter, saturn, asteroid)

    assert cutoff_angle(resonant_phase) == cutoffed_resonant_phase


@pytest.mark.parametrize('input_values, asteroid_num', [
    (['2', '-1', '-2', '0', '0', '3', '2.44125'], 2),
    (['2', '-3', '-4', '1', '1', '2', '1.44125'], 1)
])
def test_build_resonance(input_values: List[str], asteroid_num: int, resonancesfixture):
    build_resonance(input_values, asteroid_num)
    Planet1 = aliased(Planet)
    Planet2 = aliased(Planet)
    planet_q = session.query(Planet)
    asteroid_q = session.query(Asteroid)
    resonances_q = session.query(ThreeBodyResonance) \
        .join(Planet1, ThreeBodyResonance.first_body).options(joinedload('first_body')) \
        .join(Planet2, ThreeBodyResonance.second_body).options(joinedload('second_body')) \
        .join(ThreeBodyResonance.small_body).options(joinedload('small_body')) \
        .filter(and_(
        Planet1.longitude_coeff == int(input_values[0]),
        Planet1.perihelion_longitude_coeff == int(input_values[3]),

        Planet2.longitude_coeff == int(input_values[1]),
        Planet2.perihelion_longitude_coeff == int(input_values[4]),

        Asteroid.longitude_coeff == int(input_values[2]),
        Asteroid.perihelion_longitude_coeff == int(input_values[5]),
        Asteroid.axis == float(input_values[6]),
    ))

    def _check_bodies():
        """
        check values of entities from database with input values.
        :return:
        """
        resonances = resonances_q.all()  # type: List[ThreeBodyResonance]
        assert len(resonances) == 1
        planets = planet_q.all()  # type: List[Planet]
        assert len(planets) == 2
        _check(planets[0], {'name': 'JUPITER', LONG_COEFF: int(input_values[0]),
                            PERI_COEFF: int(input_values[3])})
        _check(planets[1], {'name': 'SATURN', LONG_COEFF: int(input_values[1]),
                            PERI_COEFF: int(input_values[4])})

        asteroids = asteroid_q.all()  # type: List[Asteroid]
        _check(asteroids[0], {'name': 'A%i' % asteroid_num, LONG_COEFF: int(input_values[2]),
                              PERI_COEFF: int(input_values[5])})
        assert asteroids[0].axis == float(input_values[6])
        assert len(asteroids) == 1

        assert resonances[0].first_body == planets[0]
        assert resonances[0].second_body == planets[1]
        assert resonances[0].small_body == asteroids[0]

    _check_bodies()
    build_resonance(input_values, asteroid_num)
    _check_bodies()


def _check(body, by_values: Dict):
    for key, value in by_values.items():
        assert getattr(body, key) == value
