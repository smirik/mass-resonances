import sys
from typing import Dict, List, Tuple

from catalog import build_possible_resonances
from entities import ThreeBodyResonance


def load_resonances(from_filepath: str, start_asteroid: int, stop_asteroid: int,
                    planets: Tuple[str], axis_swing: int = 0.01)\
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
    divider = 2
    toolbar_width = (stop_asteroid + 1 - start_asteroid) // divider
    sys.stdout.write("Build resonances [%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width + 1))

    res = {}
    for i in range(start_asteroid, stop_asteroid + 1):
        res[i] = build_possible_resonances(from_filepath, i, planets, axis_swing)
        if i % divider == 0:
            sys.stdout.write("#")
            sys.stdout.flush()
    sys.stdout.write("\n")
    return res
