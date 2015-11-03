from typing import List
import os

from settings import ConfigSingleton
from settings import PROJECT_DIR


class Asteroid(object):
    number = None
    resonance = None

    def __init__(self, number: int, resonance: List[float]=None):
        self.resonance = resonance
        self.number = number


class ResonanceDatabase(object):
    CONFIG = ConfigSingleton.get_singleton()
    DBPATH = os.path.join(PROJECT_DIR, CONFIG['resonance']['db_file'])

    def __init__(self, db_file: str=DBPATH):
        """

        :type db_file: str
        """

        self.db_file = db_file
        self._create_if_not_exists()

    def find_between(self, start: int, stop: int) -> List[Asteroid]:
        """Find all asteroids in resonances for given interval [start, stop]
        in body numbers.

        :param int start: start of the interval
        :param int stop: stop of the interval
        :rtype list:
        :return: list of instances of the Asteroid.
        """
        asteroids = []

        with open(self.db_file) as f:
            for line in f:
                arr = line.split(';')
                tmp = int(arr[0].strip())
                if (tmp >= start) and (tmp <= stop):
                    resonance = arr[1]
                    resonance = resonance.replace('[', '').replace(']', '')
                    resonance = [float(x) for x in resonance.split(',')]
                    asteroids.append(Asteroid(int(arr[0]), resonance))
        return asteroids

    def _create_if_not_exists(self):
        if not os.path.exists(self.db_file):
            self._create()

    def _create(self):
        dir_path = os.path.dirname(self.db_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        f = open(self.db_file, 'w')
        f.close()
