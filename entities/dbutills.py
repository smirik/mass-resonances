from typing import Tuple

from sqlalchemy import create_engine, Integer, Column
from sqlalchemy.ext.declarative import as_declarative
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

_engine = create_engine(_config.get_main_option('sqlalchemy.url'))
_Session = sessionmaker()
_Session.configure(bind=_engine)
session = _Session()


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