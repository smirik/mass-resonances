import os
from os.path import join as opjoin

import pytest

from resonances.datamining.orbitalelements import FilepathBuilder, FilepathException
from resonances.settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()

TEMP_FIXTURES = opjoin(PROJECT_DIR, 'temp_fixtures')
FIXTURES = opjoin(PROJECT_DIR, 'tests', 'fixtures')
SUB_FIXTURES = opjoin(FIXTURES, 'subdirectory')
TEST_FILE = 'test.aei'
TEST2_FILE = 'test2.aei'


@pytest.fixture()
def aei_fixture(request):
    os.mkdir(TEMP_FIXTURES)
    os.mkdir(SUB_FIXTURES)
    test_filepaths = [opjoin(SUB_FIXTURES, TEST_FILE), opjoin(TEMP_FIXTURES, TEST2_FILE)]

    for path in test_filepaths:
        with open(path, 'w') as test_file:
            test_file.write('123')

    paths = (FIXTURES, TEMP_FIXTURES)

    def fin():
        for item in test_filepaths:
            os.remove(item)
        os.rmdir(TEMP_FIXTURES)
        os.rmdir(SUB_FIXTURES)

    request.addfinalizer(fin)
    return paths


@pytest.mark.parametrize('is_recursive', [True, False])
def test_filepathbuilder(aei_fixture, is_recursive: bool):
    builder = FilepathBuilder(aei_fixture, is_recursive)
    if not is_recursive:
        with pytest.raises(FilepathException):
            assert builder.build(TEST_FILE) == opjoin(SUB_FIXTURES, TEST_FILE)
    else:
        assert builder.build(TEST_FILE) == opjoin(SUB_FIXTURES, TEST_FILE)
    assert builder.build(TEST2_FILE) == opjoin(TEMP_FIXTURES, TEST2_FILE)
