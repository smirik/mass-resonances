from typing import List
from unittest import mock
from os.path import join as opjoin
import pytest

from entities import Libration
from settings import Config

CONFIG = Config.get_params()

if 'tests' not in Config.get_project_dir():
    Config.set_project_dir(opjoin(Config.get_project_dir(), 'tests'))

LIBRATION_MIN = CONFIG['resonance']['libration']['min']
X_STOP = CONFIG['gnuplot']['x_stop']

NOT_APOCENTIC_BREAKS = [9.0, 21.0, 30.0, 39.0, 48.0, 60.0, 69.0, 78.0, 90.0,
                        99.0, 108.0, 117.0, 129.0]

PERCENTAGE_BREAKS = [9.0, 21.0, 30.0, 39.0, 48.0, 60.0, 69.0, 78.0, 90.0,
                     99.0, 108.0, 117.0, 129.0 + float(LIBRATION_MIN)]

ASTEROID_NUMBER = 1
BODY_COUNT = 100


@pytest.mark.parametrize('breaks', [None, NOT_APOCENTIC_BREAKS, [10000]])
@mock.patch('entities.ThreeBodyResonance')
def test_circulations(ThreeBodyResonanceMock, breaks: List[float]):
    resonance = ThreeBodyResonanceMock()
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.circulation_breaks == breaks


@pytest.mark.parametrize('breaks, average_delta', [
    ([], None), (NOT_APOCENTIC_BREAKS, None),
    (PERCENTAGE_BREAKS, 1548.3846153846155)
])
@mock.patch('entities.ThreeBodyResonance')
def test_average_delta(ThreeBodyResonanceMock, breaks: List[float],
                       average_delta: float):
    resonance = ThreeBodyResonanceMock()
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.average_delta == average_delta


@pytest.mark.parametrize('breaks, percentage', [
    ([], None), (NOT_APOCENTIC_BREAKS, None), (PERCENTAGE_BREAKS, 20012.)])
@mock.patch('entities.ThreeBodyResonance')
def test_percentage(ThreeBodyResonanceMock, breaks: List[float],
                    percentage: float):
    resonance = ThreeBodyResonanceMock()
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.percentage == percentage


@pytest.mark.parametrize('breaks, max_diff', [
    ([], X_STOP), (NOT_APOCENTIC_BREAKS, X_STOP - NOT_APOCENTIC_BREAKS[-1:][0]),
    (PERCENTAGE_BREAKS, X_STOP - PERCENTAGE_BREAKS[-1:][0])
])
@mock.patch('entities.ThreeBodyResonance')
def test_max_diff(ThreeBodyResonanceMock, breaks: List[float], max_diff: float):
    resonance = ThreeBodyResonanceMock()
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.max_diff == max_diff


@pytest.mark.parametrize('breaks, is_pure', [
    ([], True), (NOT_APOCENTIC_BREAKS, False), (PERCENTAGE_BREAKS, False)
])
@mock.patch('entities.ThreeBodyResonance')
def test_is_pure(ThreeBodyResonanceMock, breaks: List[float], is_pure: bool):
    resonance = ThreeBodyResonanceMock()
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.is_pure == is_pure


@pytest.mark.parametrize('breaks, is_apocentric', [
    ([], False), (NOT_APOCENTIC_BREAKS, True), (PERCENTAGE_BREAKS, True)
])
@mock.patch('entities.ThreeBodyResonance')
def test_is_transient(ThreeBodyResonanceMock, breaks: List[float],
                 is_apocentric: bool):
    resonance = ThreeBodyResonanceMock()
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.is_transient == is_apocentric


@pytest.mark.parametrize('breaks', [PERCENTAGE_BREAKS])
@mock.patch('entities.ThreeBodyResonance')
def test_as_aposentric(ThreeBodyResonanceMock, breaks: List[float]):
    resonance = ThreeBodyResonanceMock()
    resonance_str = '[1,2,3]'
    resonance.__str__ = mock.MagicMock(return_value=resonance_str)
    asteroid_num = 1
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.as_transient() == '%i;%s;%i;%f;%f' % (
        asteroid_num, resonance_str, Libration.TRANSIENT_ID,
        libration.average_delta, libration.max_diff)


@pytest.mark.parametrize('breaks', [PERCENTAGE_BREAKS])
@mock.patch('entities.ThreeBodyResonance')
def test_as_pure(ThreeBodyResonanceMock, breaks: List[float]):
    resonance = ThreeBodyResonanceMock()
    resonance_str = '[1,2,3]'
    resonance.__str__ = mock.MagicMock(return_value=resonance_str)
    asteroid_num = 1
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.as_pure() == '%i;%s;%i' % (
        asteroid_num, resonance_str, Libration.PURE_ID)


@pytest.mark.parametrize('breaks', [PERCENTAGE_BREAKS])
@mock.patch('entities.ThreeBodyResonance')
def test_as_pure_apocentric(ThreeBodyResonanceMock, breaks: List[float]):
    resonance = ThreeBodyResonanceMock()
    resonance_str = '[1,2,3]'
    resonance.__str__ = mock.MagicMock(return_value=resonance_str)
    asteroid_num = 1
    libration = Libration(resonance, breaks, BODY_COUNT)
    assert libration.as_pure_apocentric() == '%i;%s;%i' % (
        asteroid_num, resonance_str, Libration.APOCENTRIC_PURE_ID)
