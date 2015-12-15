import logging
from typing import Iterable

from commands.find.librationbuilder import get_orbitalelements_filepaths
from commands.find.librationbuilder import TransientBuilder
from commands.find.librationbuilder import ApocentricBuilder
from entities import Body
from entities import ThreeBodyResonance
from entities.dbutills import session
from integrator.calc import BigBodyOrbitalElementSet
from storage import ResonanceDatabase


def _find_resonances(start: int, stop: int) -> Iterable[ThreeBodyResonance]:
    """Find resonances from /axis/resonances by asteroid axis. Currently
    described by 7 items list of floats. 6 is integers satisfying
    D'Alembert rule. First 3 for longitutes, and second 3 for longitutes
    perihilion. Seventh value is asteroid axis.

    :param stop:
    :param start:
    :return:
    """

    names = ['A%i' % x for x in range(start, stop)]
    resonances = session.query(ThreeBodyResonance).join(ThreeBodyResonance.small_body) \
        .filter(Body.name.in_(names))

    resonances = [x for x in resonances]
    resonances = sorted(resonances, key=lambda x: x.asteroid_number)

    for resonance in resonances:
        yield resonance


def find(start: int, stop: int, is_current: bool = False):
    """Find all possible resonances for all asteroids from start to stop.

    :param is_current:
    :param stop:
    :param start:
    :return:
    """
    rdb = ResonanceDatabase('export/full.db')
    # if not is_current:
    #     try:
    #         extract(start)
    #     except FileNotFoundError as exc:
    #         logging.info('Archive %s not found. Try command \'package\'',
    #                      exc.filename)

    smallbody_filepath, firstbody_filepath, secondbody_filepath \
        = get_orbitalelements_filepaths(1)
    firstbody_elements = BigBodyOrbitalElementSet(firstbody_filepath)
    secondbody_elements = BigBodyOrbitalElementSet(secondbody_filepath)

    for resonance in _find_resonances(start, stop):
        asteroid_num = resonance.asteroid_number
        libration = resonance.libration

        if not is_current and libration is None:
            builder = TransientBuilder(asteroid_num, resonance, firstbody_elements,
                                       secondbody_elements, not is_current)
            libration = builder.build()
        elif not libration:
            continue

        if not libration.is_pure:
            if libration.is_transient:
                if libration.percentage:
                    logging.info('A%i, %s, resonance = %s', asteroid_num,
                                 str(libration), str(resonance))
                    rdb.add_string(libration.as_transient())
                    continue
                else:
                    logging.debug(
                        'A%i, NO RESONANCE, resonance = %s, max = %f',
                        asteroid_num, str(resonance), libration.max_diff
                    )
                    session.expunge(libration)

        elif not libration.is_apocentric:
            logging.info('A%i, pure resonance %s', asteroid_num, str(resonance))
            rdb.add_string(libration.as_pure())
            continue

        if not is_current and not libration.is_apocentric:
            builder = ApocentricBuilder(asteroid_num, resonance, firstbody_elements,
                                        secondbody_elements, not is_current)
            libration = builder.build()

        if libration.is_pure:
            rdb.add_string(libration.as_pure_apocentric())
            logging.info('A%i, pure apocentric resonance %s', asteroid_num,
                         str(resonance))
        else:
            session.expunge(libration)

    session.commit()
