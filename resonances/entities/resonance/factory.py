import warnings
from abc import abstractmethod
from enum import Enum, unique
from typing import Dict, Tuple
from typing import List

from resonances.entities.dbutills import engine, session
from sqlalchemy import Table
from sqlalchemy import exc as sa_exc, column, UniqueConstraint
from sqlalchemy.dialects.postgresql.psycopg2 import PGCompiler_psycopg2
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import Select, Insert, TableClause
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.sql.elements import ColumnClause
from sqlalchemy.sql.expression import Executable, ClauseElement
from sqlalchemy.sql.expression import alias
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.expression import table

from resonances.entities.body import Asteroid
from resonances.entities.body import LONG_COEFF
from resonances.entities.body import PERI_COEFF
from resonances.entities.body import Planet
from resonances.shortcuts import fix_id_sequence
from .threebodyresonance import ThreeBodyResonance
from .twobodyresonance import TwoBodyResonance

_has_upsert = None
_planet_table = Planet.__table__  # type: Table
_asteroid_table = Asteroid.__table__  # type: Table


@unique
class BodyNumberEnum(Enum):
    two = 2
    three = 3


class ResonanceFactory:
    def __init__(self, planets: Tuple[str]):
        self._planets = planets
        self._bodies = None  # type: Dict[str, Dict[str, int]]
        self._body_tables = None  # type: Dict[str, table]
        self._resonance_table = None  # type: Table
        self._resonance_cls = None

    @abstractmethod
    def _get_planets(self) -> List[Dict[str, int]]:
        pass

    @abstractmethod
    def _get_asteroid(self) -> Dict[str, int]:
        pass

    def _is_resonance_exists(self, conn) -> Tuple[bool, Select]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)
            _build_planets(conn, self._get_planets(), self._get_asteroid())

        body_clause = and_(*[_make_sql_condition(y.c, self.bodies[x])
                             for x, y in self._body_tables.items()])
        sel = select([x.c.id for x in self._body_tables.values()]).where(body_clause)
        resonance_exists = False

        if not _is_support_upsert():
            subquery = session.query(self._resonance_cls)
            for key, value in self._body_tables.items():
                subquery = subquery.join(value, getattr(self._resonance_cls, key))
            resonance_exists = session.query(subquery.filter(body_clause).exists()).scalar()

        return resonance_exists, sel

    def build(self, conn: Connection) -> int:
        """Builds query to insert resonance to DB and return id of it.

        :param conn:
        """
        resonance_exists, sel = self._is_resonance_exists(conn)
        if not resonance_exists:
            resonance_insert = _InsertFromSelect(self._resonance_table, sel,
                                                 self._resonance_cls.__table__)
            try:
                resonance_id = conn.execute(resonance_insert).first()
            except IntegrityError:
                fix_id_sequence(self._resonance_cls.__table__, conn)
                resonance_id = conn.execute(resonance_insert).first()
            return resonance_id

    @property
    def _columns(self) -> List[ColumnClause]:
        return [column('%s_id' % x) for x in self._body_tables.keys()]

    @property
    def bodies(self) -> Dict[str, Dict[str, int]]:
        return self._bodies

    @property
    def resonance_cls(self):
        return self._resonance_cls


class ThreeBodyResonanceFactory(ResonanceFactory):
    def __init__(self, data: List[str], asteroid_num: int, planets: Tuple[str]):
        super(ThreeBodyResonanceFactory, self).__init__(planets)
        self._bodies = dict(
            first_body={
                'name': self._planets[0],
                LONG_COEFF: int(data[0]),
                PERI_COEFF: int(data[3])
            },
            second_body={
                'name': self._planets[1],
                LONG_COEFF: int(data[1]),
                PERI_COEFF: int(data[4])
            },
            small_body={
                'name': 'A%s' % asteroid_num,
                LONG_COEFF: int(data[2]),
                PERI_COEFF: int(data[5]),
                'axis': float(data[6])
            }
        )
        self._body_tables = dict(
            first_body=alias(_planet_table, 'first_body'),
            second_body=alias(_planet_table, 'second_body'),
            small_body=alias(_asteroid_table, 'small_body')
        )
        self._resonance_cls = ThreeBodyResonance
        self._resonance_table = table(self._resonance_cls.__tablename__, *self._columns)

    def _get_planets(self):
        return [self.bodies['first_body'], self.bodies['second_body']]

    def _get_asteroid(self) -> Dict[str, int]:
        return self.bodies['small_body']


class TwoBodyResonanceFactory(ResonanceFactory):
    def __init__(self, data: List[str], asteroid_num: int, planets: Tuple[str]):
        super(TwoBodyResonanceFactory, self).__init__(planets)
        self._bodies = dict(
            first_body={
                'name': self._planets[0],
                LONG_COEFF: int(data[0]),
                PERI_COEFF: int(data[2])
            },
            small_body={
                'name': 'A%s' % asteroid_num,
                LONG_COEFF: int(data[1]),
                PERI_COEFF: int(data[3]),
                'axis': float(data[4])
            }
        )

        self._body_tables = dict(
            first_body=alias(_planet_table, 'first_body'),
            small_body=alias(_asteroid_table, 'small_body')
        )
        self._resonance_cls = TwoBodyResonance
        self._resonance_table = table(self._resonance_cls.__tablename__, *self._columns)

    def _get_planets(self):
        return [self.bodies['first_body']]

    def _get_asteroid(self) -> Dict[str, int]:
        return self.bodies['small_body']


def build_resonance(resonance_factory: ResonanceFactory) -> int:
    """Builds SQL query to add instance ResonanceMixin and return id of it.

    :param resonance_factory:
    :return:
    """
    conn = engine.connect()
    return resonance_factory.build(conn)


def get_resonance_factory(planets: Tuple, data: List[str],
                          asteroid_num: int) -> ResonanceFactory:
    n_planets = len(planets) + 1
    if n_planets == BodyNumberEnum.two.value:
        return TwoBodyResonanceFactory(data, asteroid_num, planets)
    if n_planets == BodyNumberEnum.three.value:
        return ThreeBodyResonanceFactory(data, asteroid_num, planets)
    assert False


def _make_sql_condition(entity_cls: ImmutableColumnCollection, from_body_attrs: Dict):
    return and_(*[getattr(entity_cls, k) == v for k, v in from_body_attrs.items()])


class _InsertFromSelect(Executable, ClauseElement):
    _execution_options = Executable._execution_options.union({'autocommit': True})

    def __init__(self, table_clause_: TableClause, select_expr: Select, table_: Table):
        self.table = table_
        self.table_clause = table_clause_
        self.select = select_expr


@compiles(_InsertFromSelect)
def _visit_insert_from_select(element: _InsertFromSelect, compiler: PGCompiler_psycopg2, **kw):
    return "INSERT INTO %s (%s) %s %s" % (
        compiler.process(element.table_clause, asfrom=True),
        ', '.join(element.table_clause.columns.keys()),
        compiler.process(element.select),
        _get_conflict_action(element.table, True)
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


def _execute_insert(by_conn: Connection, for_table: Table, insert_query):
    try:
        by_conn.execute(insert_query)
    except IntegrityError:
        fix_id_sequence(for_table, by_conn)
        by_conn.execute(insert_query)


def _build_planets(conn: Connection, planets: List[Dict[str, int]], small_body: Dict[str, int]):
    if not _is_support_upsert():
        for planet in planets:
            if not _check_body(Planet, planet):
                _execute_insert(conn, Planet.__table__,
                                _planet_table.insert(inline=True, values=planet))
        if not _check_body(Asteroid, small_body):
            _execute_insert(conn, Asteroid.__table__,
                            _asteroid_table.insert(inline=True, values=small_body))
    else:
        planet_conflict_action = _get_conflict_action(_planet_table)
        asteroid_conflict_action = _get_conflict_action(_asteroid_table)
        planet_insert = _planet_table.insert(append_string=planet_conflict_action,
                                             inline=True, values=planets)
        asteroid_insert = _asteroid_table.insert(append_string=asteroid_conflict_action,
                                                 inline=True, values=small_body)
        _execute_insert(conn, Planet.__table__, planet_insert)
        _execute_insert(conn, Asteroid.__table__, asteroid_insert)


def _check_body(cls, parametes: Dict):
    query = session.query
    return query(query(cls).filter_by(**parametes).exists()).scalar()


def _is_support_upsert() -> bool:
    global _has_upsert
    if _has_upsert is None:
        conn = engine.connect()
        version_str = [x['version'] for x in conn.execute('SELECT version();')][0]
        if '9.5' in version_str:
            _has_upsert = True
        else:
            _has_upsert = False
    return _has_upsert


def _get_conflict_action(for_table: Table, need_id: bool = False) -> str:
    """Makes part of SQL query contains action that will be produced on conflict.

    :param for_table: table which will take new record.
    :param need_id: indicates that query must return id.
    """
    from functools import reduce
    from operator import add
    unique_contraints = [x for x in for_table.constraints if isinstance(x, UniqueConstraint)]
    column_names = reduce(add, [x.columns.keys() for x in unique_contraints])
    #column_names = [x.columns.keys() for x in unique_contraints]

    if need_id and column_names:
        action = 'DO UPDATE SET {0}=EXCLUDED.{0} RETURNING id;'.format(column_names[0])
    else:
        action = 'DO NOTHING'

    if _is_support_upsert():
        serialized_fields = ('(%s)' % ', '.join(column_names)) if column_names else ''
        _conflict_action = 'on conflict %s %s' % (serialized_fields, action)
    else:
        _conflict_action = ''
    return _conflict_action
