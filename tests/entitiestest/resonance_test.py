from typing import List

from entities import ThreeBodyResonance, build_resonance
from entities.body import Planet
from entities.body import Asteroid
from entities.body import LONG
from entities.body import PERI
import pytest
from entities.epoch import Epoch
from tests.shortcuts import get_class_path
from unittest import mock
import math

from utils.shortcuts import cutoff_angle


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
def test_build_resonance(input_values: List[str], asteroid_num: int):
    resonance = build_resonance(input_values, asteroid_num, Epoch(start_day=1, end_day=2))
    assert resonance.first_body.longitude_coeff == int(input_values[0])
    assert resonance.first_body.perihelion_longitude_coeff == int(input_values[3])

    assert resonance.second_body.longitude_coeff == int(input_values[1])
    assert resonance.second_body.perihelion_longitude_coeff == int(input_values[4])

    assert resonance.small_body.longitude_coeff == int(input_values[2])
    assert resonance.small_body.perihelion_longitude_coeff == int(input_values[5])

    assert resonance.asteroid_axis == float(input_values[6])
