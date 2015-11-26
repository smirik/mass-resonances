from typing import List

import pytest
from os.path import join as opjoin
from os.path import exists as opexists
import os
from settings import Config
import settings
from storage import ResonanceDatabase
from utils.series import CirculationYearsFinder

if 'tests' not in Config.get_project_dir():
    Config.set_project_dir(opjoin(settings.Config.get_project_dir(), 'tests'))

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


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


RESFILE_DATA = """0.0000000 -0.511077 2.765030 0.077237 0.174533 1.396263 2.690092 5.203010 0.048542 9.578820 0.054070
3.0000000 0.875501 2.764430 0.078103 0.174533 1.396263 2.682815 5.203710 0.048899 9.584690 0.057297
6.0000000 2.371922 2.764580 0.078213 0.174533 1.396263 2.663383 5.201790 0.048970 9.573660 0.056652
9.0000000 -2.512588 2.765610 0.077484 0.174533 1.396263 2.662716 5.202390 0.048907 9.542190 0.053900
"""


@pytest.fixture
def res_filepath() -> str:
    filepath = opjoin(PROJECT_DIR, 'testfile.res')
    with open(filepath, 'w') as resfile:
        resfile.write(RESFILE_DATA)

    return filepath


@pytest.mark.parametrize('for_apocetric, results', [
    (False, [9.]), (True, [3.])
])
def test_getting_years(res_filepath: str, for_apocetric: bool, results: List[float]):
    finder = CirculationYearsFinder(for_apocetric, res_filepath)
    res = finder.get_years()
    assert res == results
    os.remove(res_filepath)
