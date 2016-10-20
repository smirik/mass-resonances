from typing import Tuple, List
from unittest import mock

import pytest
from abc import abstractmethod
from datamining.resonances import get_resonance_query, PLANET_TABLES
from entities.body import Planet, Asteroid
from settings import Config
from sqlalchemy.exc import InvalidRequestError

from tests.shortcuts import get_class_path
from datamining import LibrationClassifier, ResonanceOrbitalElementSetFacade
from entities import ThreeBodyResonance, get_resonance_factory, BodyNumberEnum, TwoBodyResonance, \
    ResonanceMixin, TwoBodyLibration
from entities import build_resonance
from entities import Libration
from entities.dbutills import session, engine
from tests.entitiestest.librationtest import PERCENTAGE_BREAKS

CONFIG = Config.get_params()
X_STOP = CONFIG['gnuplot']['x_stop']


@pytest.fixture(params=[
    (('JUPITER', 'SATURN'), ['1', '1', '-1', '0', '0', '3', '2.123'], 1),
    (('JUPITER',), ['1', '-1', '0', '3', '2.123'], 1)
])
def libration_resonance_fixture(request):
    build_resonance(get_resonance_factory(*request.param))

    t1 = PLANET_TABLES['first_body']
    t2 = PLANET_TABLES['second_body']

    body_count = BodyNumberEnum(len(request.param[0])+1)

    query = get_resonance_query(body_count)
    query = query.filter(
        t1.longitude_coeff == 1, Asteroid.longitude_coeff == -1, t1.perihelion_longitude_coeff == 0,
        Asteroid.perihelion_longitude_coeff == 3)
    if body_count == BodyNumberEnum.three:
        query = query.filter(t2.longitude_coeff == 1, t2.perihelion_longitude_coeff == 0)
    resonance = query.first()

    session.commit()

    def tear_down():
        conn = engine.connect()
        conn.execute(Libration.__table__.delete())
        conn.execute(TwoBodyLibration.__table__.delete())
        conn.execute(TwoBodyResonance.__table__.delete())
        conn.execute(ThreeBodyResonance.__table__.delete())
        conn.execute(Planet.__table__.delete())
        conn.execute(Asteroid.__table__.delete())

    request.addfinalizer(tear_down)

    return resonance, body_count


@pytest.mark.parametrize('circulation_breaks, is_apocentric', [
    ([], False), (PERCENTAGE_BREAKS, False),
    ([], True), (PERCENTAGE_BREAKS, True),
    ([3., 6., 9.], True)
])
@mock.patch(get_class_path(ResonanceOrbitalElementSetFacade))
@pytest.mark.usefixtures('libration_resonance_fixture')
def test_classify_from_db(ResonanceOrbitalElementSetFacadeMock,
                          libration_resonance_fixture: Tuple[ResonanceMixin, BodyNumberEnum],
                          circulation_breaks, is_apocentric):
    orbital_element_set = ResonanceOrbitalElementSetFacadeMock()

    resonance, body_count = libration_resonance_fixture
    libration_cls = Libration if body_count == BodyNumberEnum.three else TwoBodyLibration
    libration = libration_cls(resonance, circulation_breaks, X_STOP, is_apocentric)
    resonance.libration = libration
    session.commit()

    classifier = LibrationClassifier(True, body_count)
    classifier.set_resonance(resonance)
    resonant_phases = [
        {'year': 0.0, 'value': 0.0},
        {'year': 3.0, 'value': 0.0},
        {'year': 6.0, 'value': 0.0},
        {'year': 9.0, 'value': 0.0}
    ]
    if circulation_breaks == [3., 6., 9.]:
        with pytest.raises(InvalidRequestError):
            classifier.classify(orbital_element_set, resonant_phases)
    else:
        res = classifier.classify(orbital_element_set, resonant_phases)
        assert res is True


TWO_BREAK_APOCENTRIC_PHASES = [{'year': 0.0, 'value': -0.51}, {'year': 3.0, 'value': 0.87},
                               {'year': 6.0, 'value': 2.37}, {'year': 9.0, 'value': -2.51},
                               {'year': 12.0, 'value': 0.01}]

SIMPLE_PHASES = [
    {'year': 0.0, 'value': 0.0},
    {'year': 3.0, 'value': 0.0},
    {'year': 6.0, 'value': 0.0},
    {'year': 9.0, 'value': 0.0}
]


@pytest.mark.parametrize('resonant_phases, is_apocentric', [
    (SIMPLE_PHASES, False),
    (SIMPLE_PHASES, False),
    (SIMPLE_PHASES, True), (SIMPLE_PHASES, True),
    (TWO_BREAK_APOCENTRIC_PHASES, True)
])
@mock.patch(get_class_path(ResonanceOrbitalElementSetFacade))
@pytest.mark.usefixtures('libration_resonance_fixture')
def test_classify_without_db(ResonanceOrbitalElementSetFacadeMock,
                             libration_resonance_fixture: Tuple[ResonanceMixin, BodyNumberEnum],
                             resonant_phases, is_apocentric):
    orbital_element_set = ResonanceOrbitalElementSetFacadeMock()
    resonance, body_count = libration_resonance_fixture
    classifier = LibrationClassifier(False, body_count)
    classifier.set_resonance(resonance)

    res = classifier.classify(orbital_element_set, resonant_phases)
    assert res is True
    assert len(session.new) == 1
    libration = [x for x in session.new][0]
    assert libration.resonance == resonance
    assert libration == resonance.libration
    session.commit()
