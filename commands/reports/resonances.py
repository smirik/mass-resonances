from datamining.resonances import PLANET_TABLES, GetQueryBuilder
from entities import ResonanceMixin
from entities import BodyNumberEnum
from entities.body import Asteroid
from texttable import Texttable
from .shortcuts import AsteroidCondition, PlanetCondition


def show_resonance_table(asteroid_condition: AsteroidCondition = None,
                         planet_condtion: PlanetCondition = None, limit=100, offset=0,
                         body_count: int=3):
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
