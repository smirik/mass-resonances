import logging
import sys
import os
from os.path import join as opjoin
from typing import List, Tuple, Iterable
from catalog import find_by_number
from integrator import ResonanceOrbitalElementSet
from settings import Config
from storage import ResonanceDatabase
from storage.resonance_archive import extract
from utils.series import CirculationYearsFinder
from entities import build_resonance, Libration
from entities import ThreeBodyResonance
from entities.dbutills import session

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
X_STOP = CONFIG['gnuplot']['x_stop']
AXIS_SWING = CONFIG['resonance']['axis_error']
RESONANCE_TABLE_FILE = CONFIG['resonance_table']['file']
RESONANCE_FILEPATH = opjoin(PROJECT_DIR, 'axis', RESONANCE_TABLE_FILE)
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
OUTPUT_ANGLE = CONFIG['output']['angle']
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]


def _build_resonances(asteroid_num: int, by_asteroid_axis: float, with_swing: float) \
        -> List[ThreeBodyResonance]:
    res = []
    try:
        with open(RESONANCE_FILEPATH) as resonance_file:
            for line in resonance_file:
                line_data = line.split()
                resonance = build_resonance(line_data, asteroid_num)
                if abs(resonance.asteroid_axis - by_asteroid_axis) <= with_swing:
                    res.append(resonance)
    except FileNotFoundError:
        logging.error('File %s not found. Try command resonance_table.',
                      RESONANCE_FILEPATH)
        sys.exit(1)

    session.commit()
    return res


def _find_resonance_with_min_axis(by_axis: float, with_swing: float = 0.0001) \
        -> ThreeBodyResonance:
    resonances = _build_resonances(1, by_axis, with_swing)
    index_of_min_axis = 0

    def _delta(of_resonance: ThreeBodyResonance) -> float:
        return of_resonance.asteroid_axis - by_axis

    for i, resonance in enumerate(resonances):
        if _delta(resonance) < _delta(resonances[index_of_min_axis]):
            index_of_min_axis = i

    return resonances[index_of_min_axis]


def _find_resonances(start: int, stop: int) -> Iterable[Tuple[int, ThreeBodyResonance]]:
    """Find resonances from /axis/resonances by asteroid axis. Currently
    described by 7 items list of floats. 6 is integers satisfying
    D'Alembert rule. First 3 for longitutes, and second 3 for longitutes
    perihilion. Seventh value is asteroid axis.

    :param stop:
    :param start:
    :return:
    """

    delta = stop - start
    for i in range(delta + 1):
        asteroid_num = start + i
        asteroid_parameters = find_by_number(asteroid_num)
        for resonance in _build_resonances(asteroid_num, asteroid_parameters[1], AXIS_SWING):
            if resonance:
                yield asteroid_num, resonance


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
        orbital_elem_set = ResonanceOrbitalElementSet(
            resonance, firstbody_filepath, secondbody_filepath)

        if not os.path.exists(os.path.dirname(res_filepath)):
            os.makedirs(os.path.dirname(res_filepath))
        with open(res_filepath, 'w+') as resonance_file:
            for item in orbital_elem_set.get_elements(smallbody_filepath):
                resonance_file.write(item)

        return res_filepath

    rdb = ResonanceDatabase('export/full.db')
    if not is_current:
        try:
            extract(start)
        except FileNotFoundError as exc:
            logging.info('Archive %s not found. Try command \'package\'',
                         exc.filename)

    for asteroid_num, resonance in _find_resonances(start, stop):
        resonance_filepath = _prepare_resfile(asteroid_num, resonance)
        transient_finder = CirculationYearsFinder(False, resonance_filepath)
        years = transient_finder.get_years()
        libration = resonance.libration
        is_new = False
        if libration is None:
            libration = Libration(resonance, years, X_STOP)
            is_new = True

        if not libration.is_pure:
            if libration.is_transient:
                if libration.percentage:
                    # if session.query(Libration).filter_by(
                    #     asteroid_number=asteroid_num, resonance_id=resonance.id
                    # ).first():
                    #     pass
                    # else:
                    # if is_new:
                        # session.add(libration)
                        # session.refresh(resonance)
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

        else:
            logging.info('A%i, pure resonance %s', asteroid_num, str(resonance))
            rdb.add_string(libration.as_pure())
            continue

        apocentric_finder = CirculationYearsFinder(True, resonance_filepath)
        years = apocentric_finder.get_years()
        libration = Libration(resonance, years, X_STOP)
        if libration.is_pure:
            rdb.add_string(libration.as_pure_apocentric())
            logging.info('A%i, pure apocentric resonance %s', asteroid_num,
                         str(resonance))
        else:
            session.expunge(libration)

    session.commit()
