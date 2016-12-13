from .resonace_table import generate_resonance_table as gentable

from typing import Dict, List

from resonances.shortcuts import ProgressBar
from resonances.settings import Config
from resonances.catalog import PossibleResonanceBuilder
from resonances.catalog import AsteroidData


CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


def load_resonances(from_source: str, asteroids: List[AsteroidData],
                    builder: PossibleResonanceBuilder, gen: bool = False)\
        -> Dict[str, List[int]]:
    """
    Makes all possible resonances for asteroids, that pointed by half-interval.
    Orbital elements for every asteroid will got from catalog, which has pointed filepath.
    :param from_source: path to catalog.
    :param asteroids: list of tuples, every tuple contains pair of asteroid's
    name and his parameters mined from catalog.
    :param gen: indicates about need to generate data.
    :return: dictionary, where keys are number of asteroids and values are
    lists of id numbers of resonances.
    """
    if gen:
        source = gentable([x for x in builder.planets])
    else:
        with open(from_source) as fd:
            source = [x for x in fd]

    p_bar = ProgressBar(len(asteroids), 'Build resonances')
    res = {}
    for asteroid in asteroids:
        res[asteroid[0]] = builder.build(source, asteroid)
        p_bar.update()
    p_bar.fin()

    return res
