import pytest
from unittest import mock
from os.path import join as opjoin
from shutil import copyfile
import os
from settings import Config

PROJECT_DIR = Config.get_project_dir()
INTEGRATOR_PATH = opjoin(PROJECT_DIR, Config.get_params()['integrator']['dir'])


@pytest.fixture
def settings_fixture():
    params = mock.patch('settings._ParamBridge')
    params.integrator = {
        'dir': 'test_mercury'
    }

    config = mock.patch('settings.Config')
    config.get_project_dir = mock.MagicMock(return_value=opjoin(PROJECT_DIR, 'tests'))
    config.get_params = mock.MagicMock(return_value=params)
    return config


@mock.patch('settings._ParamBridge')
@mock.patch('settings.Config')
def test_set_time_interval(config_mockcls, param_mockcls):
    config_mockcls.get_project_dir = mock.MagicMock(side_effect=[
        PROJECT_DIR,
        opjoin(PROJECT_DIR, 'tests'),
        opjoin(PROJECT_DIR, 'tests')
    ])

    res_dict = {
        'integrator': {
            'dir': 'test_mercury',
            'number_of_bodies': 100,
            'files': {
                'small_bodies': 'small.in'
            },
            'start': '2455400.5'
        },
        'resonance': {
            'libration': {'min': 20000},
            'bodies': [
                'JUPITER',
                'SATURN'
            ]
        },
        'output': {
            'angle': 'output/res'
        }
    }

    params = param_mockcls()
    params.__getitem__.side_effect = lambda x: res_dict[x]
    params.integrator = {'dir': 'test_mercury'}
    params.resonance = {'libration': {'min': 20000}}
    params.INTEGRATOR_PARAM_FILENAME = 'param.in'
    params.INTEGRATOR_BIG_FILENAME = 'big.in'
    config_mockcls.get_params = mock.MagicMock(return_value=params)
    from integrator import set_time_interval

    test_integrator_path = opjoin(
        config_mockcls.get_project_dir(),
        config_mockcls.get_params().integrator['dir']
    )

    os.mkdir(test_integrator_path)

    def _copyfile(name: str):
        target = opjoin(test_integrator_path, name)
        copyfile(opjoin(INTEGRATOR_PATH, name), target)
        return target

    param_in_filepath = _copyfile(params.INTEGRATOR_PARAM_FILENAME)
    big_in_filepath = _copyfile(params.INTEGRATOR_BIG_FILENAME)

    set_time_interval(1, 2)

    startday_assert_flag = False
    stopday_assert_flag = False
    with open(param_in_filepath) as f:
        for line in f:
            startday_assert_flag = startday_assert_flag or (' start time (days)= 1' in line)
            stopday_assert_flag = stopday_assert_flag or (' stop time (days) = 2' in line)

    assert startday_assert_flag == True
    assert stopday_assert_flag == True

    startday_assert_flag = False
    with open(big_in_filepath) as f:
        for line in f:
            startday_assert_flag = startday_assert_flag or (' epoch (in days) = 1' in line)

    assert startday_assert_flag == True

    os.remove(param_in_filepath)
    os.remove(big_in_filepath)
    os.rmdir(test_integrator_path)

