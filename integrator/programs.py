import logging
import subprocess
import os

from settings import Config


CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


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


def simple_clean() -> int:
    """Execute simple_clean.sh

    :rtype int:
    :return: finish code of programm.
    :raises: MercuryProgramNotFoundException
    """
    return _execute_programm('simple_clean.sh')


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
