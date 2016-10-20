from typing import List, Dict, Tuple
from entities import get_resonance_factory, ResonanceFactory, TwoBodyResonance
from entities import BodyNumberEnum
import math
from unittest import mock
import pytest
from entities import ThreeBodyResonance, build_resonance
from entities.body import Asteroid
from entities.body import LONG
from entities.body import PERI
from entities.body import LONG_COEFF
from entities.body import PERI_COEFF
from entities.body import Planet
from tests.shortcuts import TARGET_TABLES, clear_resonance_finalizer
from entities.dbutills import session, engine
from shortcuts import cutoff_angle
from sqlalchemy.orm import Query
from sqlalchemy import and_, Table
from sqlalchemy.orm import joinedload, aliased
from tests.shortcuts import resonancesfixture, get_class_path
from sqlalchemy.exc import IntegrityError

BODY_FOREIGNS = ['first_body', 'second_body']


@mock.patch(get_class_path(Planet))
@mock.patch(get_class_path(Planet))
@mock.patch(get_class_path(Asteroid))
@pytest.mark.parametrize(
    ['jupiter', 'saturn', 'asteroid', 'cutoffed_resonant_phase',
     'jupiter_coeffs', 'saturn_coeffs', 'asteroid_coeffs'],
    [
        (
            {LONG: 2.856034797, PERI: math.radians(70.12327)},
            {LONG: 3.339293952, PERI: math.radians(124.8056)},
            {LONG: 6.551616946, PERI: math.radians(103.9978)},
            -3.137910531830559,
            {LONG: 3, PERI: 0},
            {LONG: -1, PERI: 0},
            {LONG: -1, PERI: -1}
        ),
        (
            {LONG: 6.093856353, PERI: math.radians(15.66345)},
            {LONG: 6.836146629, PERI: math.radians(88.52425)},
            {LONG: 2.795411134, PERI: math.radians(21.54496)},
            -2.8669537513497794,
            {LONG: 7, PERI: 0},
            {LONG: -2, PERI: 0},
            {LONG: -2, PERI: -3}
        ),
    ]
)
def test_compute_resonant_phase(asteroid_mockcls, jupiter_mockcls, saturn_mockcls,
                                jupiter, saturn, asteroid, cutoffed_resonant_phase,
                                jupiter_coeffs, saturn_coeffs, asteroid_coeffs):
    asteroid_mock = asteroid_mockcls()
    asteroid_mock.longitude_coeff = asteroid_coeffs[LONG]
    asteroid_mock.perihelion_longitude_coeff = asteroid_coeffs[PERI]

    jupiter_mock = jupiter_mockcls()
    jupiter_mock.longitude_coeff = jupiter_coeffs[LONG]
    jupiter_mock.perihelion_longitude_coeff = jupiter_coeffs[PERI]

    saturn_mock = saturn_mockcls()
    saturn_mock.longitude_coeff = saturn_coeffs[LONG]
    saturn_mock.perihelion_longitude_coeff = saturn_coeffs[PERI]

    resonance = ThreeBodyResonance()
    resonance.first_body = jupiter_mock
    resonance.second_body = saturn_mock
    resonance.small_body = asteroid_mock

    resonant_phase = resonance.compute_resonant_phase(jupiter, saturn, asteroid)

    assert cutoff_angle(resonant_phase) == cutoffed_resonant_phase


def _build_resonances_query(body_number: BodyNumberEnum, input_values: List[str],
                            asteroid_num: int, factory: ResonanceFactory) -> Query:
    planet_tables = [aliased(Planet) for _ in range(body_number.value - 1)]
    resonance_cls = factory.resonance_cls

    resonances_q = session.query(resonance_cls)
    for planet_table, body_foreign in zip(planet_tables, BODY_FOREIGNS):
        resonances_q = resonances_q \
            .join(planet_table, getattr(resonance_cls, body_foreign)) \
            .options(joinedload(body_foreign))

    and_args = []
    for planet_table, body_foreign in zip(planet_tables, BODY_FOREIGNS):
        body_data = factory.bodies[body_foreign]
        and_args.append(planet_table.longitude_coeff == body_data[LONG_COEFF])
        and_args.append(planet_table.perihelion_longitude_coeff == body_data[PERI_COEFF])

    body_data = factory.bodies['small_body']
    and_args += [
        Asteroid.longitude_coeff == body_data[LONG_COEFF],
        Asteroid.perihelion_longitude_coeff == body_data[PERI_COEFF],
        Asteroid.axis == body_data['axis'],
    ]

    resonances_q.join(resonance_cls.small_body).options(joinedload('small_body')) \
        .filter(and_(*and_args))
    return resonances_q


@pytest.mark.parametrize(
    'input_values, asteroid_num, asteroid_indicies, planets', [
        (['2', '-1', '-2', '0', '0', '3', '2.44125'], 2, [2, 5, 6], ('JUPITER', 'SATURN')),
        (['2', '-3', '-4', '1', '1', '2', '1.44125'], 1, [2, 5, 6], ('MARS', 'SATURN')),
        (['2', '-3', '1', '2', '1.44125'], 1, [1, 3, 4], ('JUPITER',)),
        (['2', '-3', '0', '2', '1.44125'], 2, [1, 3, 4], ('MARS',)),
    ]
)
def test_build_resonance(input_values: List[str], asteroid_num: int, asteroid_indicies: List[int],
                         planets: Tuple[str], resonancesfixture):
    factory = get_resonance_factory(planets, input_values, asteroid_num)
    build_resonance(factory)
    planet_q = session.query(Planet)
    asteroid_q = session.query(Asteroid)
    body_count = BodyNumberEnum(len(planets) + 1)
    resonances_q = _build_resonances_query(body_count, input_values, asteroid_num, factory)

    def _check_bodies():
        """
        check values of entities from database with input values.
        :return:
        """
        resonances = resonances_q.all()
        assert len(resonances) == 1
        db_planets = planet_q.all()  # type: List[Planet]
        assert len(db_planets) == body_count.value - 1

        for planet, foreign in zip(db_planets, BODY_FOREIGNS):
            _check(planet, factory.bodies[foreign])
            assert getattr(resonances[0], foreign) == planet

        asteroids = asteroid_q.all()  # type: List[Asteroid]
        _check(asteroids[0], {'name': 'A%i' % asteroid_num,
                              LONG_COEFF: int(input_values[asteroid_indicies[0]]),
                              PERI_COEFF: int(input_values[asteroid_indicies[1]])})
        assert asteroids[0].axis == float(input_values[asteroid_indicies[2]])
        assert len(asteroids) == 1
        assert resonances[0].small_body == asteroids[0]

    _check_bodies()
    build_resonance(factory)
    _check_bodies()


def _check(body, by_values: Dict):
    for key, value in by_values.items():
        assert getattr(body, key) == value


@pytest.fixture
def _constraint_fixture(request):
    def fin():
        conn = engine.connect()
        for table in TARGET_TABLES:
            conn.execute("ALTER SEQUENCE %s_id_seq RESTART WITH 1;" % table.name)
        clear_resonance_finalizer(conn)

    fin()

    request.addfinalizer(fin)


JUPITER_INTS = '1 1 0 -3 4.1509'.split()


@pytest.mark.parametrize(
    'line_data, next_line_data, planets, test_table',
    [(JUPITER_INTS, '1 2 0 -5 3.5083'.split(), [('JUPITER',), ('MARS',)], x)
     for x in (Asteroid.__table__, Planet.__table__, TwoBodyResonance.__table__)] +
    [('1 1 1 0 0 -3 4.1509'.split(), '1 2 2 0 0 -5 3.5083'.split(),
      [('JUPITER', 'SATURN'), ('MARS', 'EARTHMOO')], ThreeBodyResonance.__table__)],
    ids=['for asteroid', 'for planet', 'for two body resonance', 'for three body resonance']
)
def test_id_sequences_errors(line_data: List[str], next_line_data: List[str], planets: List[Tuple],
                             test_table: Table,
                             _constraint_fixture):
    resonance_factory = get_resonance_factory(planets[0], line_data, 1)
    build_resonance(resonance_factory)

    conn = engine.connect()
    conn.execute('ALTER SEQUENCE %s_id_seq RESTART WITH 1;' % test_table.name)

    resonance_factory = get_resonance_factory(planets[1], next_line_data, 1)
    build_resonance(resonance_factory)

    for i, entry in enumerate(session.query(test_table).all()):
        assert (i + 1) == entry.id


def _create_two_resonances(line_data: List[str], next_line_data: List[str], planets: List[Tuple]):
    resonance_factory = get_resonance_factory(planets[0], line_data, 1)
    build_resonance(resonance_factory)

    resonance_factory = get_resonance_factory(planets[1], next_line_data, 1)
    build_resonance(resonance_factory)


@pytest.mark.parametrize('line_data, next_line_data, planets, asteroid_count', [
    (JUPITER_INTS, JUPITER_INTS, [('JUPITER',), ('JUPITER',)], 1),
    (JUPITER_INTS, '1 2 0 -5 3.5083'.split(), [('JUPITER',), ('JUPITER',)], 2),
    (JUPITER_INTS, '1 1 0 -5 3.5083'.split(), [('JUPITER',), ('MARS',)], 2),
    ('1 1 1 0 0 -3 4.1509'.split(), '1 2 1 0 0 -3 4.1509'.split(),
     [('JUPITER', 'SATURN'), ('MARS', 'EARTHMOO')], 1)
], ids=['same line data', 'different axis', 'different longitude', 'three body resonance'])
def test_asteroid_count(line_data: List[str], next_line_data: List[str], planets: List[Tuple],
                        asteroid_count: int, _constraint_fixture):
    _create_two_resonances(line_data, next_line_data, planets)
    assert session.query(Asteroid).count() == asteroid_count


@pytest.mark.parametrize('line_data, next_line_data, planets, planet_count', [
    (JUPITER_INTS, JUPITER_INTS, [('JUPITER',), ('JUPITER',)], 1),
    (JUPITER_INTS, '1 2 0 -3 3.5083'.split(), [('JUPITER',), ('JUPITER',)], 1),
    (JUPITER_INTS, '1 1 1 -3 3.5083'.split(), [('JUPITER',), ('JUPITER',)], 2),
    (JUPITER_INTS, '1 1 0 -3 3.5083'.split(), [('JUPITER',), ('MARS',)], 2),
    ('1 1 1 0 0 -3 4.1509'.split(), '1 2 1 0 0 -3 4.1509'.split(),
     [('JUPITER', 'SATURN'), ('MARS', 'EARTHMOO')], 4)
], ids=['same line data', 'same longitudes', 'different longitudes',
        'different names', 'three body resonance'])
def test_planet_count(line_data: List[str], next_line_data: List[str], planets: List[Tuple],
                      planet_count: int, _constraint_fixture):
    _create_two_resonances(line_data, next_line_data, planets)
    assert session.query(Planet).count() == planet_count


@pytest.mark.parametrize('line_data, next_line_data, planets, resonance_count', [
    (JUPITER_INTS, JUPITER_INTS, [('JUPITER',), ('JUPITER',)], 1),
    (JUPITER_INTS, '1 2 0 -3 3.5083'.split(), [('JUPITER',), ('JUPITER',)], 2),
    (JUPITER_INTS, '1 1 0 -5 3.5083'.split(), [('JUPITER',), ('JUPITER',)], 2),
    (JUPITER_INTS, '1 1 0 -3 3.5083'.split(), [('JUPITER',), ('MARS',)], 2),
    ('1 1 1 0 0 -3 4.1509'.split(), '1 2 1 0 0 -3 4.1509'.split(),
     [('JUPITER', 'SATURN'), ('MARS', 'EARTHMOO')], 0)
], ids=['same line data', 'different asteroid longitudes', 'different planet longitudes',
        'different planet names', 'three body resonance'])
def test_two_body_resonance_count(line_data: List[str], next_line_data: List[str],
                                  planets: List[Tuple], resonance_count: int, _constraint_fixture):
    _create_two_resonances(line_data, next_line_data, planets)
    assert session.query(TwoBodyResonance).count() == resonance_count


JUPITER_SATURN_INTS = '1 1 1 0 0 -3 4.1509'.split()


@pytest.mark.parametrize('line_data, next_line_data, planets, resonance_count', [
    (JUPITER_INTS, JUPITER_INTS, [('JUPITER',), ('JUPITER',)], 0),
    (JUPITER_SATURN_INTS, JUPITER_SATURN_INTS,
     [('JUPITER', 'SATURN'), ('JUPITER', 'SATURN')], 1),
    (JUPITER_SATURN_INTS, JUPITER_SATURN_INTS,
     [('JUPITER', 'SATURN'), ('MARS', 'EARTHMOO')], 2),
    ('1 1 1 0 0 -3 4.1509'.split(), '1 2 1 0 0 -3 4.1509'.split(),
     [('JUPITER', 'SATURN'), ('JUPITER', 'SATURN')], 2),
], ids=['two body resonance', 'same line data', 'different planet names', 'different line data'])
def test_three_body_resonance_count(line_data: List[str], next_line_data: List[str],
                                    planets: List[Tuple], resonance_count: int,
                                    _constraint_fixture):
    _create_two_resonances(line_data, next_line_data, planets)
    assert session.query(ThreeBodyResonance).count() == resonance_count