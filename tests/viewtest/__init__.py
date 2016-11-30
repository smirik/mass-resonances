import os
from os.path import join as opjoin

import pytest

from resonances.settings import Config
from resonances.view import make_plot

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


@pytest.mark.parametrize('asteroid_number', [
    '463', '490'
])
def test_make_plot(asteroid_number):
    resfilepath = opjoin(PROJECT_DIR, 'tests', 'fixtures', 'A%s.res' % asteroid_number)
    gnufilepath = opjoin(PROJECT_DIR, 'tests', 'fixtures', 'A%s.gnu' % asteroid_number)
    pngfilepath = opjoin(PROJECT_DIR, 'tests', 'fixtures', 'A%s.png' % asteroid_number)
    make_plot(resfilepath, gnufilepath, pngfilepath)

    assert os.path.exists(pngfilepath)
    assert os.path.exists(gnufilepath)
    os.remove(pngfilepath)
    os.remove(gnufilepath)
