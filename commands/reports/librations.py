from typing import List

from shortcuts import add_integer_filter
from datamining.resonances import GetQueryBuilder, PLANET_TABLES
from entities.resonance.factory import BodyNumberEnum
from .shortcuts import AsteroidCondition, PlanetCondition, AxisInterval, ResonanceIntegers
from entities import Libration, TwoBodyLibration
from sqlalchemy.orm import aliased, contains_eager
from texttable import Texttable


def show_librations(asteroid_condition: AsteroidCondition = None,
                    planet_condtion: PlanetCondition = None,
                    is_pure: bool = None, is_apocentric: bool = None,
                    axis_interval: AxisInterval = None, integers: List[str] = None,
                    body_count=3, limit=100, offset=0):
    body_count = BodyNumberEnum(body_count)

    builder = GetQueryBuilder(body_count, True)
    resonance_cls = builder.resonance_cls
    is_three = (body_count == BodyNumberEnum.three)
    libration_cls = Libration if is_three else TwoBodyLibration
    t5 = aliased(libration_cls)
    query = builder.get_resonances()\
        .outerjoin(t5, resonance_cls.libration) \
        .options(contains_eager(resonance_cls.libration, alias=t5))\
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

    table = Texttable(max_width=120)
    witdths = [10] * body_count.value
    table.set_cols_width(witdths + [30, 15, 10, 10])
    headers = ['First planet']
    if is_three:
        headers.append('Second planet')
    headers += ['Asteroid', 'Integers and semi major axis of asteroid', 'apocentric', 'pure',
                'axis (degrees)']
    table.add_row(headers)

    for resonance in query:  # type: Libration
        libration = resonance.libration
        data = [resonance.first_body.name]
        if is_three:
            data.append(resonance.second_body.name)
        data += [
            resonance.small_body.name,
            resonance,
            '%sapocentric' % ('not ' if not libration.is_apocentric else ''),
            '%spure' % ('not ' if not libration.is_pure else ''),
            resonance.asteroid_axis
        ]
        table.add_row(data)

    print(table.draw())
