from settings import Config
from view import make_plots

CONFIG = Config.get_params()


def plot(start: int, stop: int):
    make_plots(start, stop)
