import os

from settings import ConfigSingleton
from settings import PROJECT_DIR


def add_small_body(number: int, elements: list[float]):
    """Write to file, which contains data of asteroids.

    :param number int: number of asteroid
    :param elements list: parameters
    :raises: FileNotFoundError
    :raises: IndexError
    """
    CONFIG = ConfigSingleton.get_singleton()
    ep = CONFIG['integrator']['start']
    input_dir = os.path.join(PROJECT_DIR, CONFIG['integrator']['input'])
    path = os.path.join(
        input_dir, CONFIG['integrator']['files']['small_bodies']
    )

    if not os.path.exists(input_dir):
        os.mkdir(input_dir)
    try:
        with open(path, 'a+') as fd:
            fd.write(' A%i ep=%s' % (number, ep))
            fd.write(' %s 0 0 0\n' % ' '.join(elements[1:6]))
    except FileNotFoundError as e:
        raise e
    except IndexError as e:
        raise e
