from typing import Dict, List, Tuple
import logging

from resonances.entities import ThreeBodyResonance
from .resonace_table import generate_resonance_table
from resonances.catalog import build_possible_resonances
from resonances.shortcuts import ProgressBar


def load_resonances(from_source: str, start_asteroid: int, stop_asteroid: int,
                    planets: Tuple[str], axis_swing: float = 0.01, gen: bool = False)\
        -> Dict[int, List[ThreeBodyResonance]]:
    """
    Makes all possible resonances for asteroids, that pointed by half-interval.
    Orbital elements for every asteroid will got from catalog, which has pointed filepath.
    :param axis_swing:
    :param planets:
    :param from_filepath: file path of catalog.
    :param start_asteroid: start point of half-interval.
    :param stop_asteroid: stop point of half-interval. It will be excluded.
    :return: dictionary, where keys are number of asteroids and values are lists of resonances.
    """

    if gen:
        source = generate_resonance_table(*planets)
    else:
        try:
            source = open(from_source)
        except FileNotFoundError:
            logging.error('File %s not found. Try command resonance_table.', from_source)
            exit(-1)

    p_bar = ProgressBar((stop_asteroid - start_asteroid), 'Build resonances')
    res = {}
    for i in range(start_asteroid, stop_asteroid):
        res[i] = build_possible_resonances(source, i, planets, axis_swing)
        p_bar.update()
    p_bar.fin()

    if not gen:
        source.close()
    return res
