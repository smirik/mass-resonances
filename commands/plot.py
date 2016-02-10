from entities.epoch import Epoch
from settings import Config
from view import make_plots

CONFIG = Config.get_params()


def plot(start: int, stop: int, epoch: Epoch, is_force: bool):
    make_plots(start, stop, epoch, is_force)
