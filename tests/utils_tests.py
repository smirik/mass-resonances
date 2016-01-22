import os
import pytest
from os.path import exists as opexists
from os.path import join as opjoin
from settings import Config
from storage import ResonanceDatabase

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
