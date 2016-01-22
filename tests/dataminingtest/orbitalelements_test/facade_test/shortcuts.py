from typing import List
from typing import Tuple
from unittest import mock

import pytest
from datamining import OrbitalElementSet
from datamining import OrbitalElementSetCollection
from tests.shortcuts import get_class_path


def build_orbital_collection(property_mock_values: List) \
        -> Tuple[OrbitalElementSetCollection, OrbitalElementSetCollection]:
    """
    :param property_mock_values:
    :return: objects of mock of the class OrbitalElementSetCollection.
    """
    class_path = get_class_path(OrbitalElementSetCollection)
    with mock.patch(class_path) as mock1_OrbitalElementSetCollection:
        with mock.patch(class_path) as mock2_OrbitalElementSetCollection:
            orbital_elements1 = mock.PropertyMock(return_value=property_mock_values[0])
            orbital_elements2 = mock.PropertyMock(return_value=property_mock_values[1])
            first_elems = mock1_OrbitalElementSetCollection()
            second_elems = mock2_OrbitalElementSetCollection()
            type(first_elems).orbital_elements = orbital_elements1
            type(second_elems).orbital_elements = orbital_elements2
            return first_elems, second_elems


@pytest.fixture()
def first_aei_data():
    return '0.0000000  1.541309e+02  3.172742e+02  2.76503 0.077237  10.6047' \
           ' 73.6553  80.4757  0.000000e+00'


@pytest.fixture()
def second_aei_data():
    return '3.0000000  1.537140e+02  1.924902e+02  2.76443 0.078103  10.6058' \
           ' 73.2525  80.4615  0.000000e+00'


def build_elem_set(serialize_value):
    class_path = get_class_path(OrbitalElementSet)
    with mock.patch(class_path) as mock_OrbitalElementSet:
        obj = mock_OrbitalElementSet()
        obj.serialize_as_planet.return_value = serialize_value
        return obj
