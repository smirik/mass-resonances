import logging

import os
import shutil
from catalog import find_resonances
from commands.find.librationbuilder import ApocentricBuilder
from commands.find.librationbuilder import TransientBuilder, LibrationDirector
from entities.dbutills import session
from integrator.calc import ResonanceOrbitalElementSet
from integrator.calc import build_bigbody_elements
from os.path import join as opjoin
from settings import Config
from storage import ResonanceDatabase

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
OUTPUT_ANGLE = CONFIG['output']['angle']


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

    firstbody_elements, secondbody_elements = build_bigbody_elements(
        opjoin(MERCURY_DIR, '%s.aei' % BODY1),
        opjoin(MERCURY_DIR, '%s.aei' % BODY2))
    libration_director = LibrationDirector()

    for resonance, aei_data in find_resonances(start, stop):
        asteroid_num = resonance.asteroid_number
        libration = resonance.libration

        res_filepath = opjoin(PROJECT_DIR, OUTPUT_ANGLE, 'A%i.res' % asteroid_num)
        orbital_elem_set = ResonanceOrbitalElementSet(
            firstbody_elements, secondbody_elements, resonance)
        orbital_elem_set.write_to_resfile(res_filepath, aei_data)

        if not is_current and libration is None:
            builder = TransientBuilder(resonance, orbital_elem_set, res_filepath)
            libration = libration_director.build(builder)
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
            builder = ApocentricBuilder(resonance, orbital_elem_set, res_filepath)
            libration = libration_director.build(builder)

        if libration.is_pure:
            rdb.add_string(libration.as_pure_apocentric())
            logging.info('A%i, pure apocentric resonance %s', asteroid_num,
                         str(resonance))
        else:
            session.expunge(libration)

    session.commit()
