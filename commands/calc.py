import logging
import subprocess
import os

from settings import ConfigSingleton
from settings import PROJECT_DIR
from catalog import AstDys
from mercury_bridge import add_small_body


def _execute_mercury():
    class MercuryException(Exception):
        pass

    """Execute mercury program

    :raises FileNotFoundError: if mercury not installed.
    """
    path = os.path.join(PROJECT_DIR, 'mercury')

    def _execute_programm(name):
        res = subprocess.call([os.path.join(path, name)],
                              cwd=os.path.join(path))
        if res:
            logging.error('%s finished with code %i' % (name, res))
        return res

    try:
        _execute_programm('simple_clean.sh')
        code = _execute_programm('mercury6')
        code += _execute_programm('element6')
        if code:
            raise MercuryException('Mercury6 has been finished with errors.')

    except FileNotFoundError as e:
        logging.error('Check mercury submodule in %s. It must be compiled.'
                      % path)
        raise e


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

    for i in range(num_b):
        num = i + start
        arr = AstDys.find_by_number(num)
        add_small_body(num, arr)

    logging.info('Integrating orbits...')
    _execute_mercury()
    logging.info('[done]')
