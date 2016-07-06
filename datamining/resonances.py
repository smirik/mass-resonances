"""
Module contains kit for getting resonances from databases.
"""
import logging
from typing import Dict
from typing import Iterable, Tuple, List

from datamining.orbitalelements import FilepathBuilder
from entities import ThreeBodyResonance, BodyNumberEnum, TwoBodyResonance
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


class GetQueryBuilder:
    """
    Class build base query for getting two or three body resonances or related planets.
    """
    def __init__(self, for_bodies: BodyNumberEnum):
        if for_bodies == BodyNumberEnum.three:
            self.resonance_cls = ThreeBodyResonance
        else:
            self.resonance_cls = TwoBodyResonance
        self.query = session.query(self.resonance_cls)
        self.for_bodies = for_bodies
        self._foreings = FOREIGNS[:for_bodies.value - 1]

    def get_resonances(self) -> Query:
        query = self.query.join(Asteroid, isouter=True)
        query = self._add_join(query)
        return query

    def get_planets(self) -> Query:
        cols = [PLANET_TABLES[x].name.label('%s_name1' % x) for x in self._foreings]
        query = session.query(*cols).select_from(self.resonance_cls)
        query = self._add_join(query).group_by(*cols)
        return query

    def _add_join(self, query: Query) -> Query:
        for key in self._foreings:
            planet_table = PLANET_TABLES[key]
            resonance_attr = getattr(self.resonance_cls, '%s_id' % key)
            query = query.join(planet_table, resonance_attr == planet_table.id, isouter=True)
        return query


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


def get_resonances(start: int, stop: int, only_librations: bool, planets: Tuple[str, ...]) \
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
    resonances = GetQueryBuilder(body_count).get_resonances()
    for i, key in enumerate(FOREIGNS):
        if i >= (body_count.value - 1):
            break
        resonances = resonances.filter(PLANET_TABLES[key].name == planets[i])
    resonances = resonances.filter(Asteroid.number >= start, Asteroid.number < stop)\
        .options(joinedload('libration')).order_by(Asteroid.number)

    if only_librations:
        resonances = resonances.join('libration')

    if not resonances:
        logging.info('We have no resonances, try command load-resonances --start=%i --stop=%i'
                     % (start, stop))

    for resonance in resonances:
        yield resonance


def get_aggregated_resonances(from_asteroid: int, to_asteroid: int, only_librations: bool,
                              planets: Tuple[str, ...], filepath_builder: FilepathBuilder) \
        -> Iterable[Tuple[ResonanceMixin, List[str]]]:
    """Find resonances from /axis/resonances by asteroid axis. Currently
    described by 7 items list of floats. 6 is integers satisfying
    D'Alembert rule. First 3 for longitutes, and second 3 for longitutes
    perihilion. Seventh value is asteroid axis.

    :param filepath_builder:
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

                smallbody_filepath = filepath_builder.build('A%i.aei' % self._asteroid_number)
                with open(smallbody_filepath) as aei_file:
                    for line in aei_file:
                        self._aei_data.append(line)

            return self._aei_data

    aei_getter = _DataGetter()
    for resonance in get_resonances(from_asteroid, to_asteroid, only_librations, planets):
        aei_data = aei_getter.get_aei_data(resonance.asteroid_number)
        assert len(aei_data) > 0
        yield resonance, aei_data
