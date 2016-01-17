from typing import List, Dict
import pytest
from unittest import mock
from os.path import join as opjoin
from os.path import exists as opexists
import os
from settings import Config
from storage import ResonanceDatabase
from utils.series import CirculationYearsFinder
from utils.series import NoPhaseException
from utils.series import session

CONFIG = Config.get_params()
PROJECT_DIR = opjoin(Config.get_project_dir(), 'tests')


@pytest.mark.parametrize('path', [
    opjoin(PROJECT_DIR, CONFIG['resonance']['db_file']),
    opjoin(PROJECT_DIR, 'export', 'unittest_db.txt')
])
def test_init(path: str):
    obj = ResonanceDatabase(path)
    assert obj.db_file == path
    assert opexists(obj.db_file)
    os.remove(path)
    os.removedirs(os.path.dirname(path))


@pytest.mark.parametrize('resonance_id, phase_arguments, result_years', [
    (1, [], None),
    (1, [
        {'year': 0.0, 'value': 1.32}
    ], []),
    (1, [
        {'year': 0.0, 'value': -0.51},
        {'year': 3.0, 'value': 0.87},
        {'year': 6.0, 'value': 2.37},
        {'year': 9.0, 'value': -2.51}
    ], [6.])
])
@mock.patch('entities.Phase')
def test_getting_years(Phase, monkeypatch, resonance_id, phase_arguments: List[Dict],
                       result_years: List[float]):
    class QueryMock:
        def filter_by(self, *args, **kwargs):
            return self

        def order_by(self, *args):
            return self

        def yield_per(self, number):
            return self

        def all(self):
            phase = Phase()
            year = mock.PropertyMock(side_effect=[x['year'] for x in phase_arguments])
            value = mock.PropertyMock(side_effect=[x['value'] for x in phase_arguments])
            type(phase).year = year
            type(phase).value = value
            return [phase for x in range(len(phase_arguments))]

    def query(arg):
        return QueryMock()

    monkeypatch.setattr(session, 'query', query)
    finder = CirculationYearsFinder(resonance_id, False)
    if result_years is None:
        with pytest.raises(NoPhaseException):
            finder.get_years()
    else:
        assert finder.get_years() == result_years
