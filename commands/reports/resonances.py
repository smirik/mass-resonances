from typing import List, Dict

from decimal import Decimal

from settings import Config
import os
from datamining.resonances import PLANET_TABLES, GetQueryBuilder
from entities import ResonanceMixin
from entities import BodyNumberEnum
from texttable import Texttable
from .shortcuts import AsteroidCondition, PlanetCondition
from shortcuts import add_integer_filter

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
PATH = os.path.join(PROJECT_DIR, CONFIG['catalog']['file'])
SKIP_LINES = CONFIG['catalog']['astdys']['skip']
PRECISION = 4


def get_asteroid_axises(start: int = 1, stop: int = None) -> Dict[str, float]:
    res = {}

    with open(PATH, 'r') as catalog_file:
        for i, line in enumerate(catalog_file):
            if i < start + SKIP_LINES - 1:
                continue

            line = line.split()
            asteroid_name = 'A%s' % line[0][1:-1]
            res[asteroid_name] = float(line[2])

            if stop and i >= stop + SKIP_LINES - 1:
                break
    return res


def show_resonance_table(asteroid_condition: AsteroidCondition = None,
                         planet_condtion: PlanetCondition = None, limit=100, offset=0,
                         body_count: int=3, integers: List[str] = None):
    body_count = BodyNumberEnum(body_count)
    builder = GetQueryBuilder(body_count, True)
    query = builder.get_resonances()

    if asteroid_condition:
        query = query.filter(builder.asteroid_alias.number >= asteroid_condition.start,
                             builder.asteroid_alias.number < asteroid_condition.stop)
        catalog_axises = get_asteroid_axises(asteroid_condition.start, asteroid_condition.stop)
    else:
        catalog_axises = get_asteroid_axises()

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
            table.set_cols_width(options.column_widths + [10, 10])
            table.set_precision(PRECISION)
            table.header(options.column_names + ['catalog axis', 'axis difference'])

        catalog_axis = catalog_axises[resonance.small_body.name]
        row = options.get_data(resonance) + [
            '%.5f' % catalog_axis,
            round(catalog_axis, PRECISION) - resonance.asteroid_axis
        ]
        table.add_row(row)

    print(table.draw() if table else 'No resonance by pointed filter.')
