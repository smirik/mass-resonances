import os

from settings import Config
from entities import RDB_Asteroid

from typing import List


class ResonanceDatabase(object):
    CONFIG = Config.get_params()
    PROJECT_DIR = Config.get_project_dir()
    DBPATH = os.path.join(PROJECT_DIR, CONFIG['resonance']['db_file'])

    def __init__(self, db_file: str = DBPATH):
        """

        :type db_file: str
        """

        self.db_file = db_file
        self._create_if_not_exists()

    def find_between(self, start: int, stop: int) -> List[RDB_Asteroid]:
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
                    asteroids.append(RDB_Asteroid(int(arr[0]), resonance))
        return asteroids

    def add_string(self, value: str):
        tmp = value.split(';')
        s = '%s;%s' % (tmp[0], tmp[1])
        if not self._check_string(s):
            with open(self.db_file, 'a+') as db:
                db.write('%s\n' % value)

    def _check_string(self, value: str) -> bool:
        with open(self.db_file, 'r') as f:
            for line in f:
                if value in line:
                    return True
        return False

    def _create_if_not_exists(self):
        if not os.path.exists(self.db_file):
            self._create()

    def _create(self):
        dir_path = os.path.dirname(self.db_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        f = open(self.db_file, 'w')
        f.close()
