from entities.resonance.factory import BodyNumberEnum
from .shortcuts import AsteroidCondition, PlanetCondition, AxisInterval, ResonanceIntegers
from entities import Libration, TwoBodyLibration, TwoBodyResonance
from entities import ThreeBodyResonance
from entities.body import Planet, Asteroid
from entities.dbutills import session
from sqlalchemy.orm import joinedload, aliased
from texttable import Texttable


def show_librations(asteroid_condition: AsteroidCondition = None,
                    planet_condtion: PlanetCondition = None,
                    is_pure: bool = None, is_apocentric: bool = None,
                    axis_interval: AxisInterval = None, integers: ResonanceIntegers = None,
                    body_count=3, limit=100, offset=0):
    t1 = aliased(Planet)
    t2 = aliased(Planet)
    body_count = BodyNumberEnum(body_count)
    is_three = (body_count == BodyNumberEnum.three)
    libration_cls = Libration if is_three else TwoBodyLibration
    resonances_cls = ThreeBodyResonance if is_three else TwoBodyResonance
    librations = session.query(libration_cls).options(joinedload('resonance')) \
        .join(resonances_cls) \
        .join(t1, resonances_cls.first_body_id == t1.id) \
        .options(joinedload('resonance.first_body')) \
        .options(joinedload('resonance.small_body'))
    if is_three:
        librations = librations.join(t2, ThreeBodyResonance.second_body_id == t2.id) \
            .join(Asteroid, ThreeBodyResonance.small_body_id == Asteroid.id) \
            .options(joinedload('resonance.second_body'))

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

    librations = librations.limit(limit).offset(offset)

    table = Texttable(max_width=120)
    witdths = [10] * body_count.value
    table.set_cols_width(witdths + [30, 15, 10, 10])
    headers = ['First planet']
    if is_three:
        headers.append('Second planet')
    headers += ['Asteroid', 'Integers and semi major axis of asteroid', 'apocentric', 'pure',
                'axis (degrees)']
    table.add_row(headers)

    for libration in librations:  # type: Libration
        data = [libration.resonance.first_body.name]
        if is_three:
            data.append(libration.resonance.second_body.name)
        data += [
            libration.resonance.small_body.name,
            libration.resonance,
            '%sapocentric' % ('not ' if not libration.is_apocentric else ''),
            '%spure' % ('not ' if not libration.is_pure else ''),
            libration.resonance.asteroid_axis
        ]
        table.add_row(data)

    print(table.draw())
