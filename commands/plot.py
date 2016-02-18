from settings import Config
from view import make_plots_from_db
from view import make_plots_from_redis

CONFIG = Config.get_params()


def plot(start: int, stop: int, from_db: bool):
    if from_db:
        make_plots_from_db(start, stop)
    else:
        make_plots_from_redis(start, stop)
