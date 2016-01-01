from settings import Config
from view import make_plots

CONFIG = Config.get_params()


def plot(start: int, stop: int, is_force: bool):
    make_plots(start, stop, is_force)
