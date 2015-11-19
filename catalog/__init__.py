from typing import List
import os
import logging

from settings import Config

CONFIG = Config.get_params()
SKIP_LINES = CONFIG['catalog']['astdys']['skip']
PROJECT_DIR = Config.get_project_dir()
PATH = os.path.join(PROJECT_DIR, CONFIG['catalog']['file'])


def find_by_number(number: int) -> List[float]:
    """Find asteroid parameters by number.

    :param int number: num for search.
    :return list: array contains parameters of asteroid.
    """

    try:
        with open(PATH, 'r') as f_file:
            for i, line in enumerate(f_file):
                if i < number - 1 + SKIP_LINES:
                    continue

                arr = line.split()[1:]
                arr = [float(x) for x in arr]
                arr[4], arr[5] = arr[5], arr[4]
                return arr
    except FileNotFoundError as e:
        link = 'http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat'
        logging.error('File from astdys doesn\'t exist try this %s' % link)
        raise e
