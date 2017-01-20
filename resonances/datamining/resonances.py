"""
Module contains kit for getting resonances from databases.
"""
import logging
import warnings
from os import remove
from os.path import join as opjoin
from typing import Iterable, Tuple, List, Dict
from typing import Union

from resonances.datamining.orbitalelements import FilepathBuilder
from resonances.entities import ThreeBodyResonance, BodyNumberEnum, TwoBodyResonance
from resonances.entities.dbutills import session
from resonances.entities import ResonanceMixin
from resonances.shortcuts import add_integer_filter
from sqlalchemy import exc
from sqlalchemy.orm import Query, contains_eager
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.orm.util import AliasedClass

from resonances.entities.body import Asteroid
from resonances.entities.body import Planet
from resonances.settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])

FOREIGNS = ['first_body', 'second_body']
PLANET_TABLES = {x: aliased(Planet) for x in FOREIGNS}  # type: Dict[str, Planet]
ResonanceAeiData = Tuple[ResonanceMixin, List[str]]


class GetQueryBuilder:
    """
    Class build base query for getting two or three body resonances or related planets.
    """
    def __init__(self, for_bodies: BodyNumberEnum, load_related=False):
        self._load_related = load_related
        if for_bodies == BodyNumberEnum.three:
            self.resonance_cls = ThreeBodyResonance
        else:
            self.resonance_cls = TwoBodyResonance
        self.query = session.query(self.resonance_cls)
        self.for_bodies = for_bodies
        self._foreings = FOREIGNS[:for_bodies.value - 1]
        self._asteroid_alias = aliased(Asteroid)

    def get_resonances(self) -> Query:
        query = self.query.outerjoin(self._asteroid_alias, self.resonance_cls.small_body)
        if self._load_related:
            options = contains_eager(self.resonance_cls.small_body, alias=self._asteroid_alias)
            query = query.options(options)
        query = self._add_join(query)
        return query

    @property
    def asteroid_alias(self) -> Union[AliasedClass, Asteroid]:
        return self._asteroid_alias

    def get_planets(self) -> Query:
        cols = [PLANET_TABLES[x].name.label('%s_name1' % x) for x in self._foreings]
        query = session.query(*cols).select_from(self.resonance_cls)
        query = self._add_join(query).group_by(*cols)
        return query

    def _add_join(self, query: Query) -> Query:
        for key in self._foreings:
            planet_table = PLANET_TABLES[key]

            resonance_attr = getattr(self.resonance_cls, '%s_id' % key)
            query = query.outerjoin(planet_table, resonance_attr == planet_table.id)
            if self._load_related:
                options = contains_eager(getattr(self.resonance_cls, key), alias=planet_table)
                query = query.options(options)

        return query


def get_resonances_by_asteroids(asteroids_names: Iterable[str], only_librations: bool,
                                integers: List[str], planets: tuple) -> Iterable[ResonanceMixin]:
    """Get resonances satisfyied pointed parameters."""
    body_count = BodyNumberEnum(len(planets) + 1)
    builder = GetQueryBuilder(body_count, True)
    query = builder.get_resonances()
    t1 = builder.asteroid_alias

    query = query.filter(t1.name.in_(asteroids_names))
    query = filter_by_integers(query, builder, integers)\
        .options(joinedload('libration'))

    if only_librations:
        query = query.join('libration')

    query = filter_by_planets(query, planets)

    msg = 'We have no resonances, try command load-resonances for asteroids %s' % (
        ', '.join(asteroids_names))
    yield from iterate_resonances(query, msg)


def filter_by_planets(query: Query, planets) -> Query:
    """Add filter state for query that gets resonances."""
    body_count = BodyNumberEnum(len(planets) + 1)
    for i, key in enumerate(FOREIGNS):
        if i >= (body_count.value - 1):
            break
        query = query.filter(PLANET_TABLES[key].name == planets[i])
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


def filter_by_integers(query: Query, builder: GetQueryBuilder, integers: List[int]) -> Query:
    if integers:
        tables = [PLANET_TABLES['first_body']]
        if builder.for_bodies == BodyNumberEnum.three:
            tables.append(PLANET_TABLES['second_body'])
        tables.append(builder.asteroid_alias)
        query = add_integer_filter(query, integers, tables)

    return query


def iterate_resonances(query: Query, empty_message: str) -> Iterable[ResonanceMixin]:
    is_empty = True
    for resonance in query:
        is_empty = False
        yield resonance

    if is_empty:
        logging.info(empty_message)


def get_resonances(start: int, stop: int, only_librations: bool, planets: Tuple[str, ...],
                   integers: List[str] = None) -> Iterable[ResonanceMixin]:
    """
    Returns resonances related to asteroid in pointer interval from start to stop.
    :param integers:
    :param planets:
    :param start: start of interval of asteroid numbers.
    :param stop: finish of interval of asteroid numbers.
    :param only_librations: flag indicates about getting resonances, that has related librations
    with pointed  in settings.
    :return:
    """
    body_count = BodyNumberEnum(len(planets) + 1)
    builder = GetQueryBuilder(body_count, True)
    query = builder.get_resonances()
    t1 = builder.asteroid_alias
    query = filter_by_planets(query, planets)
    query = query.filter(builder.asteroid_alias.name.op('~')('^A\d*$'))\
        .filter(t1.number >= start, t1.number < stop)\
        .options(joinedload('libration')).order_by(builder.asteroid_alias.number)

    query = filter_by_integers(query, builder, integers)
    if only_librations:
        query = query.join('libration')

    msg = 'We have no resonances, try command load-resonances --start=%i --stop=%i' % (start, stop)
    yield from iterate_resonances(query, msg)


class NoIDlistException(Exception):
    pass


def get_resonances_with_id(id_list: List[int], planets: Tuple[str, ...], integers: List[str])\
        -> Iterable[ResonanceMixin]:
    """get_resonances_with_id returns generator of resonances mined from
    database by pointed id numbers and integers satisfying D'Alambert rule.

    :param id_list:
    :param planets:
    :param integers:
    """
    if not id_list:
        raise NoIDlistException
    body_count = BodyNumberEnum(len(planets) + 1)
    builder = GetQueryBuilder(body_count, True)
    query = builder.get_resonances()
    query = filter_by_planets(query, planets)
    query = query.filter(builder.resonance_cls.id.in_(id_list))\
        .order_by(builder.asteroid_alias.name)
    if integers:
        query = filter_by_integers(query, builder, integers)
    msg = 'We have no resonances for %s' % ' '.join(planets)
    if integers:
        int_msg = 'with integers %s.' % ' '.join([str(x) for x in integers])
    else:
        int_msg = 'without integers'

    yield from iterate_resonances(query, '%s %s' % (msg, int_msg))


class AEIDataGetter:
    def __init__(self, filepath_builder: FilepathBuilder, clear: bool = False):
        self._filepath_builder = filepath_builder
        self._asteroid_name = None
        self._aei_data = []
        self._clear = clear

    def get_aei_data(self, for_asteroid_name: str) -> List[str]:
        if for_asteroid_name != self._asteroid_name:
            self._asteroid_name = for_asteroid_name
            self._aei_data.clear()

            aei_path = self._filepath_builder.build('%s.aei' % self._asteroid_name)
            with open(aei_path) as aei_file:
                for line in aei_file:
                    self._aei_data.append(line)
            if self._clear:
                remove(aei_path)

        return self._aei_data


def get_aggregated_resonances(from_asteroid: int, to_asteroid: int, only_librations: bool,
                              planets: Tuple[str, ...], aei_getter: AEIDataGetter,
                              integers: List[str] = None) \
        -> Iterable[ResonanceAeiData]:
    """Find resonances from /axis/resonances by asteroid axis. Currently
    described by 7 items list of floats. 6 is integers satisfying
    D'Alembert rule. First 3 for longitutes, and second 3 for longitutes
    perihelion. Seventh value is asteroid axis.

    :param integers:
    :param aei_getter:
    :param planets:
    :param only_librations: flag indicates about getting resonances, that has related librations.
    :param to_asteroid:
    :param from_asteroid:
    :return:
    """

    for resonance in get_resonances(from_asteroid, to_asteroid, only_librations, planets, integers):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=exc.SAWarning)
            aei_data = aei_getter.get_aei_data(resonance.small_body.name)
            assert len(aei_data) > 0
            yield resonance, aei_data
