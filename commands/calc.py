import logging
import subprocess
import os

from settings import ConfigSingleton
from settings import PROJECT_DIR
from catalog import AstDys
from mercury_bridge import add_small_body
from mercury_bridge import create_small_body_file
from mercury_bridge.programms import simple_clean
from mercury_bridge.programms import mercury6
from mercury_bridge.programms import element6


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
        logging.error('Check mercury submodule in %s. It must be compiled.'
                      % path)
        raise e


def calc(start: int):
    """Calculate

    :param start int: start is position of start element for computing.
    """
    create_small_body_file()
    CONFIG = ConfigSingleton.get_singleton()
    num_b = CONFIG['integrator']['number_of_bodies']
    logging.info(
        'Create initial conditions for asteroids from %i to %i' %
        (start, start + num_b)
    )

    for i in range(num_b):
        num = i + start
        arr = AstDys.find_by_number(num)
        add_small_body(num, arr)

    logging.info('Integrating orbits...')
    _execute_mercury()
    logging.info('[done]')
