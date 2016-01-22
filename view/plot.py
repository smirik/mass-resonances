import logging
import subprocess
from typing import List

import os
from catalog import find_resonances
from entities import ThreeBodyResonance, Phase
from entities.dbutills import engine
from datamining import build_bigbody_elements, ComputedOrbitalElementSetFacade, PhaseCountException
from os.path import join as opjoin
from settings import Config


CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
OUTPUT_ANGLE = CONFIG['output']['angle']
OUTPUT_IMAGES = opjoin(PROJECT_DIR, CONFIG['output']['images'])


def make_plots(start: int, stop: int, is_force: bool = False):
    """Calculate resonances and plot the png files for given object.

    :param is_force:
    :param int start:
    :param int stop:
    :raises ExtractError: if some problems has been appeared related to
    archive.
    """

    firstbody_elements, secondbody_elements = build_bigbody_elements(
        opjoin(MERCURY_DIR, '%s.aei' % BODY1),
        opjoin(MERCURY_DIR, '%s.aei' % BODY2))

    def _make_plot(for_resonance: ThreeBodyResonance, by_aei_data: List[str],
                   with_phases: List[float], is_for_apocentric: bool):
        res_filepath = opjoin(PROJECT_DIR, OUTPUT_ANGLE, 'A%i.res' %
                              for_resonance.asteroid_number)
        orbital_elem_set = ComputedOrbitalElementSetFacade(
            firstbody_elements, secondbody_elements, with_phases)
        orbital_elem_set.write_to_resfile(res_filepath, by_aei_data)

        gnufile_path = _create_gnuplot_file(for_resonance.asteroid_number)
        if not os.path.exists(OUTPUT_IMAGES):
            os.makedirs(OUTPUT_IMAGES)

        out_path = opjoin(OUTPUT_IMAGES, 'A%i-res%i%s.png' % (
            for_resonance.asteroid_number, for_resonance.id,
            '-apocentric' if is_for_apocentric else ''
        ))
        with open(out_path, 'wb') as image_file:
            subprocess.call(['gnuplot', gnufile_path], stdout=image_file)

    conn = engine.connect()
    for resonance, aei_data in find_resonances(start, stop):
        resonance_id = resonance.id
        apocentric_phases = []
        phases = []

        result = conn.execute(
            'SELECT value, is_for_apocentric FROM %s WHERE resonance_id=%i' %
            (Phase.__tablename__, resonance_id))
        for row in result:
            if row['is_for_apocentric']:
                apocentric_phases.append(row['value'])
            else:
                phases.append(row['value'])
        try:
            if phases:
                _make_plot(resonance, aei_data, phases, False)
            if apocentric_phases:
                _make_plot(resonance, aei_data, apocentric_phases, True)
        except PhaseCountException as e:
            logging.error('%s, resonance_id = %i', str(e), resonance_id)


CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
OUTPUT_GNU_PATH = opjoin(PROJECT_DIR, CONFIG['output']['gnuplot'])
OUTPUT_RES_PATH = opjoin(PROJECT_DIR, CONFIG['output']['angle'])


def _create_gnuplot_file(body_number):
    with open(os.path.join(PROJECT_DIR, 'output', 'multi.gnu')) as gnuplot_sample_file:
        content = gnuplot_sample_file.read()

    content = (
        content.replace('result', '%s/A%i.res' % (OUTPUT_RES_PATH, body_number))
        .replace('set xrange [0:100000]', 'set xrange [0:%i]' % CONFIG['gnuplot']['x_stop'])
        .replace('with points', 'with %s' % CONFIG['gnuplot']['type'])
    )

    if not os.path.exists(OUTPUT_GNU_PATH):
        os.makedirs(OUTPUT_GNU_PATH)

    path = opjoin(OUTPUT_GNU_PATH, 'A%i.gnu' % body_number)
    with open(path, 'w+') as gnuplot_file:
        gnuplot_file.write(content)
    return path
