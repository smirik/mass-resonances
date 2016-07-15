from typing import List

from datamining.resonances import PLANET_TABLES, GetQueryBuilder
from entities import ResonanceMixin
from entities import BodyNumberEnum
from entities.body import Asteroid
from sqlalchemy.orm import Query
from texttable import Texttable
from .shortcuts import AsteroidCondition, PlanetCondition


def _add_integer_filter(query: Query, ints: List[str]) -> Query:
    any_int = '*'
    ints_count = len(ints)
    if ints[0] != any_int:
        query = query.filter(eval("PLANET_TABLES['first_body'].longitude_coeff %s" % ints[0]))
    if ints[1] != any_int:
        table = PLANET_TABLES['second_body'] if ints_count == 3 else Asteroid
        query = query.filter(eval("table.longitude_coeff %s" % ints[1]))
    if ints_count == 3 and ints[2] != any_int:
        query = query.filter(eval("Asteroid.longitude_coeff %s" % ints[2]))
    return query


def show_resonance_table(asteroid_condition: AsteroidCondition = None,
                         planet_condtion: PlanetCondition = None, limit=100, offset=0,
                         body_count: int=3, integers: List[str] = None):
    body_count = BodyNumberEnum(body_count)
    query = GetQueryBuilder(body_count).get_resonances()

    if asteroid_condition:
        names = ['A%i' % x for x in range(asteroid_condition.start, asteroid_condition.stop)]
        query = query.filter(Asteroid.name.in_(names))

    if planet_condtion:
        if planet_condtion.first_planet_name:
            query = query.filter(PLANET_TABLES['first_body'].name ==
                                 planet_condtion.first_planet_name)
        if planet_condtion.second_planet_name:
            query = query.filter(PLANET_TABLES['second_body'].name ==
                                 planet_condtion.second_planet_name)

    if integers:
        query = _add_integer_filter(query, integers)

    query = query.limit(limit).offset(offset)
    options = None
    table = None

    for resonance in query:  # type: ResonanceMixin
        if options is None:
            options = type(resonance).get_table_options()
            table = Texttable(max_width=120)
            table.set_cols_width(options.column_widths)
            table.add_row(options.column_names)
        table.add_row(options.get_data(resonance))

    print(table.draw() if table else 'No resonance by pointed filter.')
