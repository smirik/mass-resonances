import logging
import subprocess
import os
from os.path import join as opjoin
from glob import glob

from settings import Config


CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
INTEGRATOR_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
EXTENSIONS = ['dmp', 'clo', 'out', 'tmp']


def _execute_programm(name: str) -> int:
    """Execute programm from Mercury6 appication.

    :param name str: name of programm from Mercury6 application.
    :rtype int:
    :return: finish code of programm.
    :raises: MercuryProgramNotFoundException
    """

    path = os.path.join(PROJECT_DIR, CONFIG['integrator']['dir'])
    res = subprocess.call([os.path.join(path, name)], cwd=path)
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
    return _execute_programm('mercury6')


def element6() -> int:
    """Execute element6

    :rtype int:
    :return: finish code of programm.
    :raises: MercuryProgramNotFoundException
    """
    return _execute_programm('element6')
