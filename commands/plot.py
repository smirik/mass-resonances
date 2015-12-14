from settings import Config
from storage import calc_resonances

CONFIG = Config.get_params()


def plot(start: int, stop: int, is_force: bool):
    calc_resonances(start, stop, is_force)
