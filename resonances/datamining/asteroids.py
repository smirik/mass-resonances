from typing import List
from resonances.entities import BodyNumberEnum
from .resonances import GetQueryBuilder
from .resonances import filter_by_planets
from .resonances import filter_by_integers
from .resonances import iterate_resonances
from random import sample


def get_random_asteroids(of_resonance_integers: List[str], for_planets: tuple, count: int)\
        -> List[str]:
    body_count = BodyNumberEnum(len(for_planets) + 1)
    builder = GetQueryBuilder(body_count, True)
    query = builder.get_resonances()
    query = filter_by_planets(query, for_planets)
    query = filter_by_integers(query, builder, of_resonance_integers)

    msg = 'We have no resonances for %s' % ' '.join(for_planets)
    names = sample([x.small_body.name[1:] for x in iterate_resonances(query, msg)], count)
    return names
