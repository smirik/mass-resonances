import logging
import os
import subprocess
from glob import glob
from os.path import join as opjoin

from resonances.settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
INTEGRATOR_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
EXTENSIONS = ['dmp', 'clo', 'out', 'tmp']
_DEBUG = 10


def _execute_programm(name: str, is_mute: bool = False) -> int:
    """Execute programm from Mercury6 appication.

    :param name: name of programm from Mercury6 application.
    :param is_mute: indicates about muting of invoked application.
    :rtype int:
    :return: finish code of programm.
    :raises: MercuryProgramNotFoundException
    """

    path = os.path.join(PROJECT_DIR, CONFIG['integrator']['dir'])
    stdout = subprocess.DEVNULL if is_mute else None
    res = subprocess.call([os.path.join(path, name)], cwd=path, stdout=stdout)
    if res:
        logging.error('%s finished with code %i' % (name, res))
    return res


def aei_clean():
    for filename in glob(opjoin(INTEGRATOR_DIR, '*.aei')):
        os.remove(filename)


def simple_clean(with_aei=True):
    """Execute simple_clean.sh

    :param with_aei:
    :rtype bool:
    """
    for ext in EXTENSIONS:
        for filename in glob(opjoin(INTEGRATOR_DIR, '*.%s' % ext)):
            os.remove(filename)
    if with_aei:
        aei_clean()


def mercury6() -> int:
    """Execute mercury6

    :rtype int:
    :return: finish code of programm.
    :raises: MercuryProgramNotFoundException
    """
    return _execute_programm('mercury6', logging.getLogger().getEffectiveLevel() != _DEBUG)


def element6() -> int:
    """Execute element6

    :rtype int:
    :return: finish code of programm.
    :raises: MercuryProgramNotFoundException
    """
    return _execute_programm('element6', logging.getLogger().getEffectiveLevel() != _DEBUG)
