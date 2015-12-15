import logging
import os

from settings import Config
from catalog import find_by_number
from integrator import SmallBodiesFileBuilder
from integrator.programs import simple_clean
from integrator.programs import mercury6
from integrator.programs import element6

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
SMALL_BODIES_FILENAME = CONFIG['integrator']['files']['small_bodies']


class MercuryException(Exception):
    pass


def _execute_mercury():
    """Execute mercury program

    :raises FileNotFoundError: if mercury not installed.
    """
    try:
        simple_clean()
        code = mercury6()
        code += element6()
        if code:
            raise MercuryException('Mercury6 programms has been finished with errors.')

    except FileNotFoundError as e:
        raise e


def calc(start: int, stop: int):
    """Gets from astdys catalog parameters of orbital elements. Represents them
    to small.in file and makes symlink of this file in directory of application
    mercury6.

    :param int start: start is position of start element for computing.
    :param int stop:
    """
    filepath = os.path.join(PROJECT_DIR, CONFIG['integrator']['input'],
                            SMALL_BODIES_FILENAME)
    symlink = os.path.join(PROJECT_DIR, CONFIG['integrator']['dir'],
                           SMALL_BODIES_FILENAME)
    small_bodies_storage = SmallBodiesFileBuilder(filepath, symlink)
    small_bodies_storage.create_small_body_file()
    logging.info(
        'Create initial conditions for asteroids from %i to %i',
        start, stop
    )

    for i in range(start, stop):
        arr = find_by_number(i)
        small_bodies_storage.add_body(i, arr)
    small_bodies_storage.flush()

    logging.info('Integrating orbits...')
    _execute_mercury()
    logging.info('[done]')
