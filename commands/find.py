import logging
from typing import Tuple, Iterable

import os
from abc import abstractmethod
from catalog import find_by_number
from entities import Libration, Body
from entities import ThreeBodyResonance
from entities.dbutills import session
from integrator import ResonanceOrbitalElementSet
from os.path import join as opjoin
from settings import Config
from storage import ResonanceDatabase
from utils.series import CirculationYearsFinder

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
X_STOP = CONFIG['gnuplot']['x_stop']
AXIS_SWING = CONFIG['resonance']['axis_error']
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
OUTPUT_ANGLE = CONFIG['output']['angle']
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]


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

    for resonance in resonances:
        asteroid_parameters = find_by_number(resonance.asteroid_number)
        asteroid_axis = asteroid_parameters[1]
        if abs(resonance.asteroid_axis - asteroid_axis) <= AXIS_SWING:
            yield resonance


def _get_orbitalelements_filepaths(body_number: int) -> Tuple[str, str, str]:
    mercury_dir = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
    mercury_planet_dir = mercury_dir

    body_number_start = body_number - body_number % 100
    body_number_stop = body_number_start + BODIES_COUNTER
    aei_dir = opjoin(
        PROJECT_DIR, CONFIG['export']['aei_dir'],
        '%i-%i' % (body_number_start, body_number_stop), 'aei'
    )
    aei_filepath = opjoin(aei_dir, 'A%i.aei' % body_number)
    if os.path.exists(aei_filepath):
        mercury_dir = aei_dir
        mercury_planet_dir = opjoin(
            PROJECT_DIR, CONFIG['export']['aei_dir'], 'Planets'
        )

    smallbody_filepath = opjoin(mercury_dir, 'A%i.aei' % body_number)
    firstbody_filepath = opjoin(mercury_planet_dir, '%s.aei' % BODY1)
    secondbody_filepath = opjoin(mercury_planet_dir, '%s.aei' % BODY2)

    return smallbody_filepath, firstbody_filepath, secondbody_filepath


def find(start: int, stop: int, is_current: bool = False):
    """Find all possible resonances for all asteroids from start to stop.

    :param is_current:
    :param stop:
    :param start:
    :return:
    """

    def _prepare_resfile(asteroid_num: int, resonance: ThreeBodyResonance) -> str:
        smallbody_filepath, firstbody_filepath, secondbody_filepath \
            = _get_orbitalelements_filepaths(asteroid_num)
        res_filepath = opjoin(PROJECT_DIR, OUTPUT_ANGLE, 'A%i.res' % asteroid_num)
        logging.debug("Check asteroid %i", asteroid_num)
        if not is_current:
            orbital_elem_set = ResonanceOrbitalElementSet(
                resonance, firstbody_filepath, secondbody_filepath)
            if not os.path.exists(os.path.dirname(res_filepath)):
                os.makedirs(os.path.dirname(res_filepath))
            with open(res_filepath, 'w+') as resonance_file:
                for item in orbital_elem_set.get_elements(smallbody_filepath):
                    resonance_file.write(item)

        return res_filepath

    rdb = ResonanceDatabase('export/full.db')
    # if not is_current:
    #     try:
    #         extract(start)
    #     except FileNotFoundError as exc:
    #         logging.info('Archive %s not found. Try command \'package\'',
    #                      exc.filename)

    count = 0

    class AbstractLibrationBuilder:
        def __init__(self, asteroid_number: int, libration_resonance: ThreeBodyResonance):
            self._resonance = libration_resonance
            self._res_filepath = _prepare_resfile(asteroid_number, self._resonance)

        def build(self) -> Libration:
            finder = self._get_finder()
            return Libration(self._resonance, finder.get_years(), X_STOP,
                             self.is_apocetric())

        @abstractmethod
        def _get_finder(self) -> CirculationYearsFinder:
            pass

        @abstractmethod
        def is_apocetric(self) -> bool:
            pass

    class TransientBuilder(AbstractLibrationBuilder):
        def _get_finder(self) -> CirculationYearsFinder:
            transient_finder = CirculationYearsFinder(False, self._res_filepath)
            return transient_finder

        def is_apocetric(self) -> bool:
            return False

    class ApocentricBuilder(AbstractLibrationBuilder):
        def _get_finder(self) -> CirculationYearsFinder:
            apocentric_finder = CirculationYearsFinder(True, self._res_filepath)
            return apocentric_finder

        def is_apocetric(self) -> bool:
            return True

    class LibrationDirector:
        def __init__(self, libration_builder: AbstractLibrationBuilder):
            self._builder = libration_builder

        def build(self) -> Libration:
            return self._builder.build()

    for resonance in _find_resonances(start, stop):
        asteroid_num = resonance.asteroid_number
        count += 1
        libration = resonance.libration

        if not is_current and libration is None:
            builder = TransientBuilder(asteroid_num, resonance)
            libration = LibrationDirector(builder).build()
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
            # session.expunge(libration)
            builder = ApocentricBuilder(asteroid_num, resonance)
            libration = LibrationDirector(builder).build()

        if libration.is_pure:
            rdb.add_string(libration.as_pure_apocentric())
            logging.info('A%i, pure apocentric resonance %s', asteroid_num,
                         str(resonance))
        else:
            session.expunge(libration)

    session.commit()
