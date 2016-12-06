from .resonace_table import generate_resonance_table as gentable

from typing import Dict, List

from resonances.entities import ThreeBodyResonance
from resonances.shortcuts import ProgressBar
from resonances.settings import Config
from resonances.catalog import PossibleResonanceBuilder

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


def load_resonances(from_source: str, start_asteroid: int, stop_asteroid: int,
                    builder: PossibleResonanceBuilder, gen: bool = False)\
        -> Dict[int, List[ThreeBodyResonance]]:
    """
    Makes all possible resonances for asteroids, that pointed by half-interval.
    Orbital elements for every asteroid will got from catalog, which has pointed filepath.
    :param axis_swing:
    :param planets:
    :param from_filepath: file path of catalog.
    :param start_asteroid: start point of half-interval.
    :param stop_asteroid: stop point of half-interval. It will be excluded.
    :param gen: indicates about need to generate data.
    :return: dictionary, where keys are number of asteroids and values are lists of resonances.
    """

    if gen:
        source = gentable([x for x in builder.planets])
    else:
        with open(from_source) as fd:
            source = [x for x in fd]

    p_bar = ProgressBar((stop_asteroid - start_asteroid), 'Build resonances')
    res = {}
    for i in range(start_asteroid, stop_asteroid):
        res[i] = builder.build(source, i)
        p_bar.update()
    p_bar.fin()

    return res
