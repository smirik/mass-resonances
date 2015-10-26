import logging
import subprocess
import os

from settings import ConfigSingleton
from settings import PROJECT_DIR
from catalog import AstDys
from mercury_bridge import add_small_body

class Command(object):
    @staticmethod
    def _execute_mercury():
        """Execute mercury program

        :raises FileNotFoundError: if mercury not installed.
        """
        path = os.path.join(PROJECT_DIR, 'mercury')
        try:
            subprocess.call([os.path.join(path, 'simple_clean.sh')])
            subprocess.call([os.path.join(path, 'mercury6')])
            subprocess.call([os.path.join(path, 'element6')])
        except FileNotFoundError as e:
            logging.error('Check mercury submodule in %s. It must be compiled.'
                          % path)
            raise e

    @staticmethod
    def calc(start: int):
        """Calculate

        :param start int: start is position of start element for computing.
        """
        CONFIG = ConfigSingleton.get_singleton()
        num_b = CONFIG['integrator']['number_of_bodies']
        logging.info(
            'Create initial conditions for asteroids from #%i to #%i' %
            (start, start + num_b)
        )

        for i in num_b['times']:
            num = i + start
            arr = AstDys.find_by_number(num)
            add_small_body(num, arr)

        logging.info('Integrating orbits...')
        Command._execute_mercury()
        logging.info('[done]')
