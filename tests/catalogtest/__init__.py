from typing import List, Tuple
from unittest import mock

import pytest
from catalog import find_by_number
from entities.dbutills import session
from settings import Config
from entities import ThreeBodyResonance, BodyNumberEnum
from datamining import get_aggregated_resonances
from tests.shortcuts import get_class_path
from tests.shortcuts import resonancesfixture

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


@pytest.mark.parametrize('number, catalog_values',
                         [(1, [57400.0, 2.7681116175738203, 0.07575438197786899, 10.59165825139208,
                               72.73329603027756, 80.32179293568826, 181.38128433921716, 3.41,
                               0.12]),
                          (2, [57400.0, 2.772362122525498, 0.2310236014408419, 34.84094939488245,
                               309.98944656158335, 173.0882797978601, 163.60442273654294, 4.09,
                               0.11])])
def test_find_by_number(number: int, catalog_values: List[float]):
    assert find_by_number(number) == catalog_values


def _resonance_mock(resonance_str, asteroid_number):
    with mock.patch(get_class_path(ThreeBodyResonance)) as ThreeBodyResonance_mock:
        resonance = ThreeBodyResonance_mock()
        resonance.__str__ = mock.MagicMock(return_value=resonance_str)
        resonance.asteroid_number = asteroid_number
        return resonance


@pytest.mark.parametrize('start, stop, resonances_str, planets', [
    (1, 3, ['[4 -2 -1 0 0 2.1468]', '[1 -1 -7 0 0 1.1641]'], ('JUPITER', 'SATURN')),
    (3, 4, [], ('MARS', 'JUPITER')),
    (1, 3, ['[4 -1 0 2.1468]', '[1 -7 0 1.1641]'], ('MARS',)),
    (3, 4, [], ('JUPITER',))
])
def test_find_resonances(resonancesfixture, start, stop, resonances_str,
                         planets: Tuple[str], monkeypatch):
    class QueryMock:
        def filter(self, *args, **kwargs):
            return self

        def join(self, *args, **kwargs):
            return self

        def options(self, *args, **kwargs):
            return self

        def all(self):
            res = []
            for i, resonance_str in enumerate(resonances_str):
                res.append(_resonance_mock(resonance_str, i + start))
            return res

    def query(arg):
        return QueryMock()

    monkeypatch.setattr(session, 'query', query)
    if not resonances_str:
        assert [x for x in get_aggregated_resonances(start, stop, False, planets)] == []
    else:
        for i, (resonance, aei_data) in enumerate(get_aggregated_resonances(
                start, stop, False, planets)):
            assert str(resonance) == resonances_str[i]
