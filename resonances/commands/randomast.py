from typing import Tuple
from typing import List
from resonances.datamining import get_random_asteroids as _get_random_asteroids
from resonances.catalog import read_header
from resonances.settings import Config


def get_random_asteroids(for_integers: List[int], for_planets: Tuple[str], count: int):
    names = _get_random_asteroids(for_integers, for_planets, count)
    print(' '.join(names))
