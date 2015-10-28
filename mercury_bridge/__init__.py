from typing import List
import os

from settings import ConfigSingleton
from settings import PROJECT_DIR

CONFIG = ConfigSingleton.get_singleton()


def add_small_body(number: int, elements: List[float]):
    """Write to file, which contains data of asteroids.

    :param number int: number of asteroid
    :param elements list: parameters
    :raises: FileNotFoundError
    :raises: IndexError
    """
    ep = CONFIG['integrator']['start']
    input_dir = os.path.join(PROJECT_DIR, CONFIG['integrator']['input'])
    path = os.path.join(
        input_dir, CONFIG['integrator']['files']['small_bodies']
    )

    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    try:
        with open(path, 'a+') as fd:
            fd.write(' A%i ep=%s' % (number, ep))
            fd.write(' %s 0 0 0\n' % ' '.join([str(x) for x in elements[1:6]]))
    except FileNotFoundError as e:
        raise e
    except IndexError as e:
        raise e


def calc(body_number: int, resonance: List[float], is_full: bool = False):
    pass


def create_small_body_file():
    header = ")O+_06 Small-body initial data  (WARNING: Do not delete this line!!)\n" \
             ") Lines beginning with `)' are ignored.\n" \
             ")---------------------------------------------------------------------\n" \
             " style (Cartesian, Asteroidal, Cometary) = Ast" \
             "\n)---------------------------------------------------------------------\n"
    filename = os.path.join(
        PROJECT_DIR,
        CONFIG['integrator']['input'],
        CONFIG['integrator']['files']['small_bodies']
    )
    fd = open(filename, 'w')
    fd.write(header)
    fd.close()
