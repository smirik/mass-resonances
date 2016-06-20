from datamining.resonances import GetQueryBuilder
from entities import BodyNumberEnum
from texttable import Texttable


def show_planets(body_count: int):
    body_count = BodyNumberEnum(body_count)
    builder = GetQueryBuilder(body_count)
    query = builder.get_planets()
    table = Texttable(max_width=80)
    for item in query:
        table.add_row(item)

    print(table.draw())
