from typing import List

from resonances.datamining.resonances import GetQueryBuilder, PLANET_TABLES
from resonances.entities import Libration, TwoBodyLibration
from sqlalchemy.orm import Query
from sqlalchemy.orm import aliased, contains_eager
from texttable import Texttable

from resonances.entities.resonance import BodyNumberEnum
from resonances.shortcuts import add_integer_filter
from .shortcuts import AsteroidCondition, PlanetCondition, AxisInterval


def _build_libration_query(asteroid_condition: AsteroidCondition,
                           planet_condtion: PlanetCondition,
                           is_pure: bool, is_apocentric: bool,
                           axis_interval: AxisInterval, integers: List[str],
                           body_count: BodyNumberEnum, limit=100, offset=0) -> Query:

    builder = GetQueryBuilder(body_count, True)
    resonance_cls = builder.resonance_cls
    is_three = (body_count == BodyNumberEnum.three)
    libration_cls = Libration if is_three else TwoBodyLibration
    t5 = aliased(libration_cls)
    query = builder.get_resonances() \
        .outerjoin(t5, resonance_cls.libration) \
        .options(contains_eager(resonance_cls.libration, alias=t5)) \
        .filter(t5.id.isnot(None))

    t1 = PLANET_TABLES['first_body']
    t2 = PLANET_TABLES['second_body']
    t3 = builder.asteroid_alias

    if asteroid_condition:
        query = query.filter(t3.number >= asteroid_condition.start,
                             t3.number < asteroid_condition.stop)

    if planet_condtion:
        if planet_condtion.first_planet_name:
            query = query.filter(t1.name == planet_condtion.first_planet_name)
        if planet_condtion.second_planet_name:
            query = query.filter(t2.name == planet_condtion.second_planet_name)

    if is_pure is not None:
        query = query.filter(t5.is_pure == is_pure)

    if is_apocentric is not None:
        query = query.filter(t5.is_apocentric == is_apocentric)

    if axis_interval:
        query = query.filter(t3.axis > axis_interval.start, t3.axis < axis_interval.stop)

    if integers:
        tables = [t1]
        if is_three:
            tables.append(t2)
        tables.append(t3)
        query = add_integer_filter(query, integers, tables)

    query = query.limit(limit).offset(offset)
    return query


def dump_librations(asteroid_condition: AsteroidCondition = None,
                    planet_condtion: PlanetCondition = None,
                    is_pure: bool = None, is_apocentric: bool = None,
                    axis_interval: AxisInterval = None, integers: List[str] = None,
                    body_count=3, limit=100, offset=0):
    body_count = BodyNumberEnum(body_count)
    query = _build_libration_query(asteroid_condition, planet_condtion, is_pure, is_apocentric,
                                   axis_interval, integers, body_count, limit, offset)

    headers = ['ID', 'asteroid',
               'first_planet_longitude', 'second_planet_longitude', 'asteroid_longitude', 'axis',
               'first_planet', 'second_planet',
               'pure', 'apocentric']
    print(';'.join(headers))
    for resonance in query:  # type: ResonanceMixin
        libration = resonance.libration
        data = [str(libration.id), resonance.small_body.name[1:]]
        data += [str(x.longitude_coeff) for x in resonance.get_big_bodies()]
        data.append(str(resonance.small_body.longitude_coeff))
        data.append(str(resonance.asteroid_axis))
        data += [x.name for x in resonance.get_big_bodies()]
        data += [
            '%d' % libration.is_pure,
            '%d' % libration.is_apocentric,
        ]
        print(';'.join(data))


def show_librations(asteroid_condition: AsteroidCondition = None,
                    planet_condtion: PlanetCondition = None,
                    is_pure: bool = None, is_apocentric: bool = None,
                    axis_interval: AxisInterval = None, integers: List[str] = None,
                    body_count=3, limit=100, offset=0):
    body_count = BodyNumberEnum(body_count)
    is_three = (body_count == BodyNumberEnum.three)
    query = _build_libration_query(asteroid_condition, planet_condtion, is_pure, is_apocentric,
                                   axis_interval, integers, body_count, limit, offset)
    table = Texttable(max_width=120)
    witdths = [10] * body_count.value
    table.set_cols_width(witdths + [30, 15, 10, 10])
    headers = ['First planet']
    if is_three:
        headers.append('Second planet')
    headers += ['Asteroid', 'Integers and semi major axis of asteroid', 'apocentric', 'pure',
                'axis (degrees)']
    table.add_row(headers)

    for resonance in query:  # type: ResonanceMixin
        libration = resonance.libration
        data = [x.name for x in resonance.get_big_bodies()]
        data += [
            resonance.small_body.name,
            resonance,
            '%sapocentric' % ('not ' if not libration.is_apocentric else ''),
            '%spure' % ('not ' if not libration.is_pure else ''),
            resonance.asteroid_axis
        ]
        table.add_row(data)

    print(table.draw())
