from typing import List
from unittest import mock

import pytest

from resonances.datamining import OrbitalElementSet
from resonances.datamining import OrbitalElementSetCollection
from tests.shortcuts import get_class_path

import pandas as pd


def build_orbital_collection(property_mock_values: List) \
        -> List[OrbitalElementSetCollection]:
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
            type(first_elems).__len__ = mock.MagicMock(return_value=len(property_mock_values[0]))

            if type(property_mock_values[0]) == pd.DataFrame:
                type(first_elems).__getitem__ = mock.MagicMock(
                    return_value=property_mock_values[0].loc[0])
            else:
                type(first_elems).__getitem__ = mock.MagicMock(
                    return_value=property_mock_values[0][0])

            type(second_elems).orbital_elements = orbital_elements2
            type(second_elems).__len__ = mock.MagicMock(return_value=len(property_mock_values[1]))
            if type(property_mock_values[1]) == pd.DataFrame:
                type(first_elems).__getitem__ = mock.MagicMock(
                    return_value=property_mock_values[1].loc[0])
            else:
                type(second_elems).__getitem__ = mock.MagicMock(
                    return_value=property_mock_values[1][0])

            return [first_elems, second_elems]


def build_orbital_collection_set(property_mock_values: List) \
        -> List[OrbitalElementSetCollection]:
    """
    :param property_mock_values:
    :return: objects of mock of the class OrbitalElementSetCollection.
    """
    def _first_get_item(i: int):
        return property_mock_values[0][i]

    def _second_get_item(i: int):
        return property_mock_values[1][i]

    class_path = get_class_path(OrbitalElementSetCollection)
    with mock.patch(class_path) as mock1_OrbitalElementSetCollection:
        with mock.patch(class_path) as mock2_OrbitalElementSetCollection:
            orbital_elements1 = mock.PropertyMock(return_value=property_mock_values[0])
            orbital_elements2 = mock.PropertyMock(return_value=property_mock_values[1])
            first_elems = mock1_OrbitalElementSetCollection()
            second_elems = mock2_OrbitalElementSetCollection()

            type(first_elems).orbital_elements = orbital_elements1
            type(first_elems).__len__ = mock.MagicMock(return_value=len(property_mock_values[0]))
            type(first_elems).__getitem__ = mock.MagicMock(side_effect=_first_get_item)

            type(second_elems).orbital_elements = orbital_elements2
            type(second_elems).__len__ = mock.MagicMock(return_value=len(property_mock_values[1]))
            type(second_elems).__getitem__ = mock.MagicMock(side_effect=_second_get_item)

            return [first_elems, second_elems]


@pytest.fixture()
def first_aei_data():
    return '0.0000000  1.541309e+02  3.172742e+02  2.76503 0.077237  10.6047' \
           ' 73.6553  80.4757  0.000000e+00'


@pytest.fixture()
def second_aei_data():
    return '3.0000000  1.537140e+02  1.924902e+02  2.76443 0.078103  10.6058' \
           ' 73.2525  80.4615  0.000000e+00'


@pytest.fixture()
def third_aei_data():
    return '19.9876797  1.539926E+02  9.863090E+01  2.76589 0.078327  10.5864' \
            ' 73.9825  80.0102  0.000000E+00'

from typing import Iterable

def build_elem_set(serialize_values: Iterable[str]):
    import pandas as pd
    import numpy as np

    values = []
    for serialize_value in serialize_values:
        vals = [float(x) for x in serialize_value.split()]
        values.append(vals)

    obj = pd.DataFrame(
        [{'Time (years)': 0, 'a': vals[0], 'e': vals[1],
          'long': vals[0], 'M': vals[0] - np.degrees(vals[1])}
         for vals in values],
        dtype=float)
    return obj
    # class_path = get_class_path(OrbitalElementSet)
    # with mock.patch(class_path) as mock_OrbitalElementSet:
        # obj = mock_OrbitalElementSet()
        # obj.serialize_as_planet.return_value = serialize_value
        # m_longitude, p_longitude = serialize_value.split()
        # type(obj).m_longitude = mock.PropertyMock(return_value=float(m_longitude))
        # type(obj).p_longitude = mock.PropertyMock(return_value=float(p_longitude))
        # return obj
