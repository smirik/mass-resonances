from typing import List, Dict

from resonances.entities import BodyNumberEnum
from resonances.shortcuts import add_integer_filter
from texttable import Texttable

from resonances.datamining.resonances import PLANET_TABLES, GetQueryBuilder
from resonances.settings import Config
from .shortcuts import AsteroidCondition, PlanetCondition

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
SKIP_LINES = CONFIG['catalog']['astdys']['skip']
PRECISION = 4


def _get_asteroid_axises(from_catalog: str, start: int = 1, stop: int = None) -> Dict[str, float]:
    res = {}

    with open(from_catalog, 'r') as catalog_file:
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
                         body_count: int=3, integers: List[str] = None, catalog_path: str = None):
    body_count = BodyNumberEnum(body_count)
    builder = GetQueryBuilder(body_count, True)
    query = builder.get_resonances()

    if asteroid_condition:
        query = query.filter(builder.asteroid_alias.number >= asteroid_condition.start,
                             builder.asteroid_alias.number < asteroid_condition.stop)
    catalog_axises = None
    if catalog_path:
        if asteroid_condition:
            catalog_axises = _get_asteroid_axises(catalog_path, asteroid_condition.start,
                                                  asteroid_condition.stop)
        else:
            catalog_axises = _get_asteroid_axises(catalog_path)

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

        if catalog_axises is not None:
            catalog_axis = catalog_axises[resonance.small_body.name]
            axis_diff = round(catalog_axis, PRECISION) - resonance.asteroid_axis
            catalog_axis = '%.5f' % catalog_axis
        else:
            catalog_axis = '-'
            axis_diff = '-'

        row = options.get_data(resonance) + [
            catalog_axis, axis_diff
        ]
        table.add_row(row)

    print(table.draw() if table else 'No resonance by pointed filter.')
