from typing import Tuple
import redis

from sqlalchemy import create_engine, Integer, Column
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import ClauseElement
from alembic.config import Config as AlembicConfig
import os
from settings import Config


_config = AlembicConfig(os.path.join(
    Config.get_project_dir(), Config.get_params()['db_path']
))


@as_declarative()
class Base(object):
    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)
    id = Column(Integer, primary_key=True)

engine = create_engine(_config.get_main_option('sqlalchemy.url'))
_Session = sessionmaker()
_Session.configure(bind=engine)
session = _Session()    # type: Session

_conn = redis.ConnectionPool(
    host=Config.get_params()['redis']['host'],
    port=Config.get_params()['redis']['port'],
    db=Config.get_params()['redis']['db'])
REDIS = redis.Redis(connection_pool=_conn)


def get_or_create(cls: type, **kwargs):
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
