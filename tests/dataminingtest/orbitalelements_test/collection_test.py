from math import radians
from os.path import join as opjoin

import pytest
from resonances.datamining import OrbitalElementSet
from resonances.datamining import OrbitalElementSetCollection

from resonances.datamining.orbitalelements.collection import AEIValueError
from resonances.settings import Config

PROJECT_DIR = Config.get_project_dir()
PARAMS = Config.get_params()
A1_AEI_FILE_LEN = 46


def test_orbital_elements():
    filepath = opjoin(PROJECT_DIR, PARAMS['integrator']['dir'], 'A1.aei')
    collection = OrbitalElementSetCollection(filepath)
    assert len(collection.orbital_elements) == A1_AEI_FILE_LEN
    assert len(collection) == A1_AEI_FILE_LEN
    orbitalelements = collection.orbital_elements[0]

    assert orbitalelements == collection[0]
    assert orbitalelements.time == 0.0000000
    assert orbitalelements.p_longitude == radians(1.541309E+02)
    assert orbitalelements.mean_anomaly == radians(3.172742E+02)
    assert orbitalelements.semi_axis == 2.76503
    assert orbitalelements.eccentricity == 0.077237
    assert orbitalelements.inclination == radians(int(10.6047))
    assert orbitalelements.node == radians(int(80.4757))


@pytest.fixture()
def first_aei_data():
    return '0.0000000  1.541309e+02  3.172742e+02  2.76503 0.077237  10.6047' \
           ' 73.6553  80.4757  0.000000e+00'


@pytest.fixture()
def second_aei_data():
    return '3.0000000  1.537140e+02  1.924902e+02  2.76443 0.078103  10.6058' \
           ' 73.2525  80.4615  0.000000e+00'


@pytest.mark.parametrize('data, m_longitude', [
    (first_aei_data(), 8.227571105693121), (second_aei_data(), 6.042403174232952)
])
def test_m_longitude(data, m_longitude):
    elems = OrbitalElementSet(data)
    assert elems.m_longitude == m_longitude


def test_init():
    with pytest.raises(IndexError):
        OrbitalElementSet('')

    with pytest.raises(AEIValueError):
        OrbitalElementSet('qw')


@pytest.mark.parametrize('data, mean_motion', [
    (first_aei_data(), 0.003741378704687707), (second_aei_data(), 0.0037425968304990198)
])
def test_mean_motion(data, mean_motion):
    assert OrbitalElementSet(data).mean_motion == mean_motion


@pytest.mark.parametrize('data, serialized_string', [
    (first_aei_data(), '2.765030 0.077237 0.174533 1.396263 2.690092'),
    (second_aei_data(), '2.764430 0.078103 0.174533 1.396263 2.682815')
])
def test_serialize_as_asteroid(data, serialized_string):
    assert OrbitalElementSet(data).serialize_as_asteroid() == serialized_string


@pytest.mark.parametrize('data, serialized_string', [
    (first_aei_data(), '2.765030 0.077237'), (second_aei_data(), '2.764430 0.078103')
])
def test_serialize_as_planet(data, serialized_string):
    assert OrbitalElementSet(data).serialize_as_planet() == serialized_string
