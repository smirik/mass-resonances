from typing import List, Dict

from random import random

from math import pi
import pytest
from tests.shortcuts import get_class_path
from view import make_plots_from_db
from view import make_plots_from_redis
from entities.dbutills import REDIS, engine
from entities.dbutills import session
import json
from unittest import mock
from entities import ThreeBodyResonance
import os
from os.path import join as opjoin
from settings import Config
import shutil

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()

OUTPUT_IMAGES = opjoin(PROJECT_DIR, CONFIG['output']['images'])
OUTPUT_GNU_PATH = opjoin(PROJECT_DIR, CONFIG['output']['gnuplot'])
OUTPUT_RES_PATH = opjoin(PROJECT_DIR, CONFIG['output']['angle'])

PHASES = [
    {'year': 0.0, 'value': -0.51},
    {'year': 3.0, 'value': 0.87},
    {'year': 6.0, 'value': 2.37},
    {'year': 9.0, 'value': -2.51}
]


@pytest.fixture()
def folderfixture(request):
    def tear_down():
        try:
            shutil.rmtree(os.path.dirname(OUTPUT_RES_PATH))
        except FileNotFoundError:
            pass

    request.addfinalizer(tear_down)


def _build_query_method():
    with mock.patch(get_class_path(ThreeBodyResonance)) as ThreeBodyResonance_mock:
        class QueryMock:
            def filter(self, *args, **kwargs):
                return self

            def join(self, *args, **kwargs):
                return self

            def all(self):
                resonance = ThreeBodyResonance_mock()
                resonance.__str__ = mock.MagicMock(return_value='[4 -2 -1 0 0 2.1468]')
                resonance.asteroid_number = 1
                return [resonance]

        def query(arg):
            return QueryMock()

        return query


@pytest.mark.parametrize('phase_arguments, folders_exist', [
    (PHASES, False),
    ([{'year': x * 3, 'value': random() * 2 * pi - pi} for x in range(33334)], True)
])
def test_make_plots_from_database(monkeypatch, phase_arguments: List[Dict[str, float]],
                                  folders_exist: bool, folderfixture):
    class ConnectMock:
        def execute(self, *args, **kwargs):
            return phase_arguments

    def connect():
        return ConnectMock()

    monkeypatch.setattr(engine, 'connect', connect)
    monkeypatch.setattr(session, 'query', _build_query_method())
    make_plots_from_db(1, 2)

    if not folders_exist:
        assert not os.path.exists(OUTPUT_IMAGES)
    else:
        assert len(os.listdir(OUTPUT_IMAGES)) == 2
        assert len(os.listdir(OUTPUT_GNU_PATH)) == 1
        assert len(os.listdir(OUTPUT_RES_PATH)) == 1


@pytest.mark.parametrize('phase_arguments, folders_exist', [
    (PHASES, False),
    ([{'year': x * 10, 'value': random() * 2 * pi - pi} for x in range(33334)], True)
])
def test_make_plots_from_redis(monkeypatch, phase_arguments: List[Dict[str, float]],
                               folders_exist: bool, folderfixture):
    monkeypatch.setattr(session, 'query', _build_query_method())

    def lrange(*args, **kwargs):
        return [json.dumps(x).encode() for x in phase_arguments]

    monkeypatch.setattr(REDIS, 'lrange', lrange)
    make_plots_from_redis(1, 2)

    if not folders_exist:
        assert not os.path.exists(OUTPUT_IMAGES)
    else:
        assert len(os.listdir(OUTPUT_IMAGES)) == 2
        assert len(os.listdir(OUTPUT_GNU_PATH)) == 1
        assert len(os.listdir(OUTPUT_RES_PATH)) == 1
