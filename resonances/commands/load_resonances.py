from .resonace_table import generate_resonance_table as gentable

from typing import Dict, List, Iterable

from resonances.entities import ThreeBodyResonance
from resonances.shortcuts import ProgressBar
from resonances.settings import Config
from resonances.catalog import PossibleResonanceBuilder
from resonances.catalog import AsteroidData


CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


def load_resonances(from_source: str, asteroids: List[AsteroidData],
                    builder: PossibleResonanceBuilder, gen: bool = False)\
        -> Dict[int, List[ThreeBodyResonance]]:
    """
    Makes all possible resonances for asteroids, that pointed by half-interval.
    Orbital elements for every asteroid will got from catalog, which has pointed filepath.
    :param axis_swing:
    :param planets:
    :param from_source: data of catalog.
    :param asteroids:
    :param gen: indicates about need to generate data.
    :return: dictionary, where keys are number of asteroids and values are lists of resonances.
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
