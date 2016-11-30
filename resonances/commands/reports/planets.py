from resonances.datamining.resonances import GetQueryBuilder
from resonances.entities import BodyNumberEnum, Libration
from sqlalchemy import func
from texttable import Texttable

from resonances.entities.libration import TwoBodyLibration


def show_planets(body_count: int):
    body_count = BodyNumberEnum(body_count)
    libration_cls = Libration if body_count == BodyNumberEnum.three else TwoBodyLibration
    builder = GetQueryBuilder(body_count)
    query = builder.get_planets()\
        .outerjoin(libration_cls,
                   libration_cls.__table__.c.resonance_id == builder.resonance_cls.id)\
        .add_column(func.count(builder.resonance_cls.id))\
        .add_column(func.count(libration_cls.id))
    table = Texttable(max_width=80)
    table.add_row(['%s planet' % (x+1) for x in range(body_count.value - 1)] +
                  ['resonances', 'librations'])
    for item in query:
        table.add_row(item)

    print(table.draw())
