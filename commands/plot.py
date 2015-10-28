import os

from settings import ConfigSingleton
from settings import PROJECT_DIR
from utils import ResonanceDatabase
from utils.resonance_archive import calc_resonances

CONFIG = ConfigSingleton.get_singleton()


def plot(start: int, stop: int):
    num_b = CONFIG['integrator']['number_of_bodies']

    path = CONFIG['resonance']['db_file']
    path = os.path.join(PROJECT_DIR, path)
    rdb = ResonanceDatabase(path)
    asteroids = rdb.find_between(start, stop)

    # Divide by num_b
    min = asteroids[0].number
    max = asteroids[asteroids.size-1].number

    calc_resonances(start, stop, False)
