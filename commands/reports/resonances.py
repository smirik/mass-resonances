from typing import List

from datamining.resonances import PLANET_TABLES, GetQueryBuilder
from entities import ResonanceMixin
from entities import BodyNumberEnum
from texttable import Texttable
from .shortcuts import AsteroidCondition, PlanetCondition, add_integer_filter


def show_resonance_table(asteroid_condition: AsteroidCondition = None,
                         planet_condtion: PlanetCondition = None, limit=100, offset=0,
                         body_count: int=3, integers: List[str] = None):
    body_count = BodyNumberEnum(body_count)
    builder = GetQueryBuilder(body_count, True)
    query = builder.get_resonances()

    if asteroid_condition:
        query = query.filter(builder.asteroid_alias.number >= asteroid_condition.start,
                             builder.asteroid_alias.number < asteroid_condition.stop)

    if planet_condtion:
        if planet_condtion.first_planet_name:
            query = query.filter(PLANET_TABLES['first_body'].name ==
                                 planet_condtion.first_planet_name)
        if planet_condtion.second_planet_name:
            query = query.filter(PLANET_TABLES['second_body'].name ==
                                 planet_condtion.second_planet_name)

    if integers:
        tables = [PLANET_TABLES['first_body']]
        if body_count == BodyNumberEnum.three:
            tables.append(PLANET_TABLES['second_body'])
        tables.append(builder.asteroid_alias)
        query = add_integer_filter(query, integers, tables)

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
