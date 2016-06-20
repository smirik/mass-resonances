import logging
from typing import Dict, Generic
from typing import Iterable, Tuple, List, TypeVar
from entities import ThreeBodyResonance, Libration, BodyNumberEnum, TwoBodyResonance
from entities.body import Asteroid
from entities.body import Planet
from entities.dbutills import session
from entities.resonance.twobodyresonance import ResonanceMixin
from os.path import join as opjoin
from settings import Config
from sqlalchemy.orm import Query
from sqlalchemy.orm import joinedload, aliased

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])

FOREIGNS = ['first_body', 'second_body']
PLANET_TABLES = {x: aliased(Planet) for x in FOREIGNS}  # type: Dict[str, Planet]


def get_resonance_query(for_bodies: BodyNumberEnum) -> Query:
    """
    Make select query for getting two or three body resonances.
    :param for_bodies: is need for pointing the type of resonances.
    :return:
    """
    if for_bodies == BodyNumberEnum.three:
        resonance_cls = ThreeBodyResonance
    else:
        resonance_cls = TwoBodyResonance

    query = session.query(resonance_cls) \
        .options(joinedload('small_body')).join(resonance_cls.small_body)

    for i, key in enumerate(FOREIGNS):
        if i >= (for_bodies.value - 1):
            break
        planet_table = PLANET_TABLES[key]
        resonance_attr = getattr(resonance_cls, '%s_id' % key)
        query = query.join(planet_table, resonance_attr == planet_table.id) \
            .options(joinedload(key))

    return query


def get_resonances(start: int, stop: int, only_librations: bool, planets: Tuple[str]) \
        -> Iterable[ResonanceMixin]:
    """
    Returns resonances related to asteroid in pointer interval from start to stop.
    :param planets:
    :param start: start of interval of asteroid numbers.
    :param stop: finish of interval of asteroid numbers.
    :param only_librations: flag indicates about getting resonances, that has related librations
    with pointed  in settings.
    :return:
    """
    body_count = BodyNumberEnum(len(planets) + 1)
    resonances = get_resonance_query(body_count)
    for i, key in enumerate(FOREIGNS):
        if i >= (body_count.value - 1):
            break
        resonances.filter(PLANET_TABLES[key].name == planets[i])
    names = ['A%i' % x for x in range(start, stop)]
    resonances = resonances.filter(Asteroid.name.in_(names)).options(joinedload('libration'))

    if only_librations:
        resonances = resonances.join('libration')
    resonances = sorted(resonances.all(), key=lambda x: x.asteroid_number)

    if not resonances:
        logging.info('We have no resonances, try command load-resonances --start=%i --stop=%i'
                     % (start, stop))

    for resonance in resonances:
        yield resonance


def get_aggregated_resonances(from_asteroid: int, to_asteroid: int, only_librations: bool,
                              planets: Tuple[str])\
        -> Iterable[Tuple[ResonanceMixin, List[str]]]:
    """Find resonances from /axis/resonances by asteroid axis. Currently
    described by 7 items list of floats. 6 is integers satisfying
    D'Alembert rule. First 3 for longitutes, and second 3 for longitutes
    perihilion. Seventh value is asteroid axis.

    :param planets:
    :param only_librations: flag indicates about getting resonances, that has related librations.
    :param to_asteroid:
    :param from_asteroid:
    :return:
    """

    class _DataGetter:
        def __init__(self):
            self._asteroid_number = None
            self._aei_data = []

        def get_aei_data(self, for_asteroid_number: int) -> List[str]:
            if for_asteroid_number != self._asteroid_number:
                self._asteroid_number = for_asteroid_number
                self._aei_data.clear()

                smallbody_filepath = opjoin(MERCURY_DIR, 'A%i.aei' % self._asteroid_number)
                with open(smallbody_filepath) as aei_file:
                    for line in aei_file:
                        self._aei_data.append(line)

            return self._aei_data

    aei_getter = _DataGetter()
    for resonance in get_resonances(from_asteroid, to_asteroid, only_librations, planets):
        aei_data = aei_getter.get_aei_data(resonance.asteroid_number)
        assert len(aei_data) > 0
        yield resonance, aei_data
