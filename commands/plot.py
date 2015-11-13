from settings import ConfigSingleton
from storage import calc_resonances

CONFIG = ConfigSingleton.get_singleton()


def plot(start: int, stop: int):
    calc_resonances(start, stop, False)
