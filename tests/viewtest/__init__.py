from typing import List, Dict

from random import random

from math import pi
import pytest
from tests.shortcuts import get_class_path
from view import make_plots
from entities.dbutills import REDIS
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


@pytest.mark.parametrize('phase_arguments, folders_exist', [
    (PHASES, False),
    ([{'year': x * 3, 'value': random() * 2 * pi - pi} for x in range(33334)], True)
])
@mock.patch(get_class_path(ThreeBodyResonance))
def test_make_plots(ThreeBodyResonance_mock, monkeypatch, phase_arguments: List[Dict[str, float]],
                    folders_exist: bool, folderfixture):
    def lrange(*args, **kwargs):
        return [json.dumps(x).encode() for x in phase_arguments]

    monkeypatch.setattr(REDIS, 'lrange', lrange)

    class QueryMock:
        def filter(self, *args, **kwargs):
            return self

        def join(self, *args, **kwargs):
            return self

        def all(self):
            resonance = ThreeBodyResonance_mock()
            resonance.__str__ = mock.MagicMock(return_value='[4 -2 -1 0 0 2.1468]')
            resonance.asteroid_number = 1
            # value = mock.PropertyMock(side_effect=[x['value'] for x in phase_arguments])
            # type(phase).value = value
            return [resonance]

    def query(arg):
        return QueryMock()

    monkeypatch.setattr(session, 'query', query)
    make_plots(1, 2, False)

    if not folders_exist:
        assert not os.path.exists(OUTPUT_IMAGES)
    else:
        assert len(os.listdir(OUTPUT_IMAGES)) == 2
        assert len(os.listdir(OUTPUT_GNU_PATH)) == 1
        assert len(os.listdir(OUTPUT_RES_PATH)) == 1
