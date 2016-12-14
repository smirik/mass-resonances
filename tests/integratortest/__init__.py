import os
from os.path import join as opjoin
from shutil import copyfile

from resonances.settings import Config

PROJECT_DIR = Config.get_project_dir()
INTEGRATOR_PATH = opjoin(PROJECT_DIR, Config.get_params()['integrator']['dir'])
PARAMS = Config.get_params()


def test_set_time_interval():
    from resonances.integrator import set_time_interval

    def _copyfile(name: str):
        path = opjoin(INTEGRATOR_PATH, name)
        target = opjoin(INTEGRATOR_PATH, name + '.backup')
        copyfile(path, target)
        return path

    param_in_filepath = _copyfile(PARAMS.INTEGRATOR_PARAM_FILENAME)

    set_time_interval(1, 2)

    startday_assert_flag = False
    stopday_assert_flag = False
    with open(param_in_filepath) as f:
        for line in f:
            startday_assert_flag = startday_assert_flag or (' start time (days)= 1' in line)
            stopday_assert_flag = stopday_assert_flag or (' stop time (days) = 2' in line)

    assert startday_assert_flag
    assert stopday_assert_flag

    os.remove(param_in_filepath)
    os.rename(param_in_filepath + '.backup', param_in_filepath)
