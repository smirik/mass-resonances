from entities import Libration
from entities import ThreeBodyResonance
from entities.body import Planet, Asteroid
from entities.dbutills import session
from sqlalchemy.orm import joinedload, aliased
from texttable import Texttable


class AsteroidCondition:
    def __init__(self, start, stop):
        self.stop = stop
        self.start = start


class PlanetCondition:
    def __init__(self, first_planet_name: str = None, second_planet_name: str = None):
        self.second_planet_name = second_planet_name
        self.first_planet_name = first_planet_name


class AxisInterval:
    def __init__(self, start: float, stop: float):
        self.stop = stop
        self.start = start


class ResonanceIntegers:
    def __init__(self, first, second, third):
        self.third = third
        self.second = second
        self.first = first


def show_librations(asteroid_condition: AsteroidCondition = None,
                    planet_condtion: PlanetCondition = None,
                    is_pure: bool = None, is_apocentric: bool = None,
                    axis_interval: AxisInterval = None,
                    integers: ResonanceIntegers = None):
    t1 = aliased(Planet)
    t2 = aliased(Planet)
    librations = session.query(Libration).options(joinedload('resonance'))\
        .join(ThreeBodyResonance)\
        .join(t1, ThreeBodyResonance.first_body_id == t1.id) \
        .join(t2, ThreeBodyResonance.second_body_id == t2.id) \
        .join(Asteroid, ThreeBodyResonance.small_body_id == Asteroid.id) \
        .options(joinedload('resonance.first_body')) \
        .options(joinedload('resonance.second_body')) \
        .options(joinedload('resonance.small_body'))

    if asteroid_condition:
        names = ['A%i' % x for x in range(asteroid_condition.start, asteroid_condition.stop)]
        librations = librations.filter(Asteroid.name.in_(names))

    if planet_condtion:
        if planet_condtion.first_planet_name:
            librations = librations.filter(t1.name == planet_condtion.first_planet_name)
        if planet_condtion.second_planet_name:
            librations = librations.filter(t2.name == planet_condtion.second_planet_name)

    if is_pure is not None:
        librations = librations.filter(Libration.is_pure == is_pure)

    if is_apocentric is not None:
        librations = librations.filter(Libration.is_apocentric == is_apocentric)

    if axis_interval:
        librations = librations.filter(Asteroid.axis > axis_interval.start,
                                       Asteroid.axis < axis_interval.stop)

    if integers:
        librations = librations.filter(
            t1.longitude_coeff == integers.first,
            t2.longitude_coeff == integers.second,
            Asteroid.longitude_coeff == integers.third
        )

    table = Texttable(max_width=120)
    table.set_cols_width([10, 10, 10, 30, 15, 10, 10])
    table.add_row(['First planet',
                   'Second second',
                   'Asteroid',
                   'Integers and semi major axis of asteroid',
                   'apocentric',
                   'pure',
                   'axis (degrees)'])
    for libration in librations:    # type: Libration
        table.add_row([libration.resonance.first_body.name,
                       libration.resonance.second_body.name,
                       libration.resonance.small_body.name,
                       libration.resonance,
                       '%sapocentric' % ('not ' if not libration.is_apocentric else ''),
                       '%spure' % ('not ' if not libration.is_pure else ''),
                       libration.resonance.asteroid_axis
                       ])

    print(table.draw())
