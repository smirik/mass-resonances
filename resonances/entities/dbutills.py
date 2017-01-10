import logging
import os
import time
from typing import Tuple
from typing import TypeVar
import redis
from alembic.config import Config as AlembicConfig
from sqlalchemy.sql.expression import Executable
from sqlalchemy import create_engine, Integer, Column
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql import Insert
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql.psycopg2 import PGCompiler_psycopg2

from resonances.settings import Config

CONFIG = Config.get_params()
_HOST = CONFIG['postgres']['host']
_USER = CONFIG['postgres']['user']
_PASSWORD = CONFIG['postgres']['password']
_DB = CONFIG['postgres']['db']
T = TypeVar('T')

if CONFIG['debug']:
    logging.basicConfig()
    logger = logging.getLogger("myapp.sqltime")
    logger.setLevel(logging.DEBUG)

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
        logger.debug("Start Query: %s", statement % parameters)

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        logger.debug("Query Complete!")
        logger.debug("Total Time: %f", total)

_config = AlembicConfig(os.path.join(
    Config.get_project_dir(), Config.get_params()['db_path']
))


@as_declarative()
class Base(object):
    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)
    id = Column(Integer, primary_key=True)

engine = create_engine('postgres://%s:%s@%s/%s' % (_USER, _PASSWORD, _HOST, _DB),
                       implicit_returning=False)
_Session = sessionmaker()
_Session.configure(bind=engine)
session = _Session()    # type: Session

_conn = redis.ConnectionPool(
    host=Config.get_params()['redis']['host'],
    port=Config.get_params()['redis']['port'],
    db=Config.get_params()['redis']['db'])
REDIS = redis.Redis(connection_pool=_conn)


def get_or_create(cls: type, **kwargs) -> Tuple[T, bool]:
    """
    :param kwargs:
    :param type cls:
    :rtype: Tuple[cls, bool]
    :return:
    """
    instance = session.query(cls).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        instance = cls(**params)
        session.add(instance)
        return instance, True


class OnConflictInsert(Executable, ClauseElement):
    def __init__(self, insert_expr: Insert, indexes=None):
        self.insert = insert_expr
        self._returning = None
        self.table = insert_expr.table
        self.indexes = indexes


@compiles(OnConflictInsert)
def on_conflict(elem: OnConflictInsert, compiler: PGCompiler_psycopg2, **kw):
    query_string = compiler.visit_insert(elem.insert, **kw)  # type: str
    action = 'ON CONFLICT %s DO NOTHING'
    if elem.indexes:
        fields = '(%s)' % ', '.join(elem.indexes)
        action = action % fields
    else:
        action = action % ''
    return '%s %s' % (query_string, action)
