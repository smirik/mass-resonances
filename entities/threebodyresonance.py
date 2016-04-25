import warnings
from typing import Dict
from typing import List

from settings import Config
from sqlalchemy import exc as sa_exc
from entities.body import LONG
from entities.body import PERI
from entities.body import LONG_COEFF
from entities.body import PERI_COEFF
from entities.body import Planet
from entities.body import Asteroid
from entities.dbutills import Base, engine, session
from sqlalchemy.dialects.postgresql.psycopg2 import PGCompiler_psycopg2
from sqlalchemy.engine import Connection
from sqlalchemy.sql import Select, Insert
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.expression import table
from sqlalchemy.sql.expression import column
from sqlalchemy.sql.expression import alias
from sqlalchemy import Column, Table
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement

_conflict_action = None
_planet_table = Planet.__table__  # type: Table
_asteroid_table = Asteroid.__table__  # type: Table
CONFIG = Config.get_params()
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]


def _get_conflict_action():
    global _conflict_action
    if _conflict_action is None:
        conn = engine.connect()
        version_str = [x['version'] for x in conn.execute('SELECT version();')][0]
        if '9.5' in version_str:
            _conflict_action = 'on conflict DO NOTHING'
        else:
            _conflict_action = ''
    return _conflict_action


class ThreeBodyResonance(Base):
    """ Represents three body resonance. Stores coeffitients that satisfy rule
    D'Alambert and axis of related asteroid.
    """
    __tablename__ = 'resonance'
    __table_args__ = (UniqueConstraint(
        'first_body_id', 'second_body_id', 'small_body_id',
        name='uc_first_second_small'
    ),)

    first_body_id = Column(Integer, ForeignKey('planet.id'), nullable=False)
    first_body = relationship('Planet', foreign_keys=first_body_id)  # type: Planet
    second_body_id = Column(Integer, ForeignKey('planet.id'), nullable=False)
    second_body = relationship('Planet', foreign_keys=second_body_id)  # type: Planet
    small_body_id = Column(Integer, ForeignKey('asteroid.id'), nullable=False)
    small_body = relationship('Asteroid', foreign_keys=small_body_id,  # type: Asteroid
                              backref=backref('resonances'))

    @hybrid_property
    def asteroid_axis(self):
        return self.small_body.axis

    @hybrid_property
    def asteroid_number(self) -> int:
        name = self.small_body.name
        return int(name[1:])

    def __str__(self):
        return '[%i %i %i %i %i %i %f]' % (
            self.first_body.longitude_coeff,
            self.second_body.longitude_coeff,
            self.small_body.longitude_coeff,
            self.first_body.perihelion_longitude_coeff,
            self.second_body.perihelion_longitude_coeff,
            self.small_body.perihelion_longitude_coeff,
            self.small_body.axis
        )

    def compute_resonant_phase(self, first_body: Dict[str, float],
                               second_body: Dict[str, float],
                               small_body: Dict[str, float]) -> float:
        """Computes resonant phase by linear combination of coeffitients
        satisfying D'Alambert rule and pointed longitudes.

        :param first_body:
        :param second_body:
        :param small_body:
        :return:
        """
        return (self.first_body.longitude_coeff * first_body[LONG] +
                self.first_body.perihelion_longitude_coeff * first_body[PERI] +
                self.second_body.longitude_coeff * second_body[LONG] +
                self.second_body.perihelion_longitude_coeff * second_body[PERI] +
                self.small_body.longitude_coeff * small_body[LONG] +
                self.small_body.perihelion_longitude_coeff * small_body[PERI])


def build_resonance(data: List[str], asteroid_num: int) -> ThreeBodyResonance:
    """Builds instance of ThreeBodyResonance by passed list of string values.

    :param asteroid_num:
    :param data:
    :return:
    """
    conn = engine.connect()
    first_body = {
        'name': BODY1,
        LONG_COEFF: int(data[0]),
        PERI_COEFF: int(data[3])
    }
    second_body = {
        'name': BODY2,
        LONG_COEFF: int(data[1]),
        PERI_COEFF: int(data[4])
    }
    small_body = {
        'name': 'A%i' % asteroid_num,
        LONG_COEFF: int(data[2]),
        PERI_COEFF: int(data[5]),
        'axis': float(data[6])
    }

    column_names = ['first_body_id', 'second_body_id', 'small_body_id']
    t1 = alias(_planet_table, 'first_body')
    t2 = alias(_planet_table, 'second_body')
    t3 = alias(_asteroid_table, 'small_body')
    t4 = table(ThreeBodyResonance.__tablename__, *[column(x) for x in column_names])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        _build_planets(conn, first_body, second_body, small_body)

    body_clause = and_(_make_sql_condition(t1.c, first_body),
                       _make_sql_condition(t2.c, second_body),
                       _make_sql_condition(t3.c, small_body))
    sel = select([t1.c.id, t2.c.id, t3.c.id]).where(body_clause)
    resonance_exists = False
    if not _get_conflict_action():
        resonance_exists = session.query(session.query(ThreeBodyResonance)
                                         .join(t1, ThreeBodyResonance.first_body)
                                         .join(t2, ThreeBodyResonance.second_body)
                                         .join(t3, ThreeBodyResonance.small_body)
                                         .filter(body_clause).exists()).scalar()
    if not resonance_exists:
        conn.execute(_InsertFromSelect(t4, sel))


def _make_sql_condition(entity_cls: ImmutableColumnCollection, from_body_attrs: Dict):
    return and_(*[getattr(entity_cls, k) == v for k, v in from_body_attrs.items()])


class _InsertFromSelect(Executable, ClauseElement):
    _execution_options = Executable._execution_options.union({'autocommit': True})

    def __init__(self, table_: Table, select_expr: Select):
        self.table = table_
        self.select = select_expr


@compiles(_InsertFromSelect)
def _visit_insert_from_select(element: _InsertFromSelect, compiler: PGCompiler_psycopg2, **kw):
    return "INSERT INTO %s (%s) %s %s" % (
        compiler.process(element.table, asfrom=True),
        ', '.join(element.table.c.keys()),
        compiler.process(element.select),
        _get_conflict_action()
    )


@compiles(Insert)
def _append_string(insert_expr: Insert, compiler: PGCompiler_psycopg2, **kw):
    """
    Works only with inline insert
    :param insert_expr:
    :param compiler:
    :param kw:
    :return:
    """
    query_string = compiler.visit_insert(insert_expr, **kw)
    if 'append_string' in insert_expr.kwargs:
        return query_string + " " + insert_expr.kwargs['append_string']
    return query_string


def _build_planets(conn: Connection, first_body, second_body, small_body):
    conflict_action = _get_conflict_action()
    if not conflict_action:
        if not _check_body(Planet, first_body):
            conn.execute(_planet_table.insert(inline=True, values=first_body))
        if not _check_body(Planet, second_body):
            conn.execute(_planet_table.insert(inline=True, values=second_body))
        if not _check_body(Asteroid, small_body):
            conn.execute(_asteroid_table.insert(inline=True, values=small_body))
    else:
        conn.execute(_planet_table.insert(append_string=conflict_action, inline=True,
                                          values=[first_body, second_body]))
        conn.execute(_asteroid_table.insert(append_string=conflict_action, inline=True,
                                            values=small_body))


def _check_body(cls, parametes: Dict):
    query = session.query
    return query(query(cls).filter_by(**parametes).exists()).scalar()
