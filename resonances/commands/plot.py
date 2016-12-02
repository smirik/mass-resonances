import logging
import os
import shutil
import tarfile
from math import pi
from os.path import join as opjoin
from typing import List, Tuple

from resonances.datamining import AEIDataGetter, PhaseBuilder, ResonanceOrbitalElementSetFacade
from resonances.datamining import ComputedOrbitalElementSetFacade
from resonances.datamining import PhaseLoader, PhaseStorage
from resonances.datamining import build_bigbody_elements
from resonances.datamining import get_aggregated_resonances
from resonances.datamining.orbitalelements import FilepathBuilder
from resonances.shortcuts import create_aws_s3_key
from resonances.shortcuts import cutoff_angle
from resonances.shortcuts import is_s3 as _is_s3
from resonances.shortcuts import is_tar as _is_tar

from resonances.settings import Config
from resonances.view import make_plot

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])


def plot(start: int, stop: int, phase_storage: PhaseStorage, for_librations: bool,
         integers: List[str], aei_paths: Tuple[str, ...], is_recursive: bool, planets: Tuple[str],
         output: str, build_phases: bool):
    is_s3 = _is_s3(output)
    is_tar = _is_tar(output)
    tarf = None
    s3_bucket_key = None

    if is_tar:
        output_dir = opjoin(PROJECT_DIR, '.output')
    else:
        output_dir = output

    if is_s3:
        if not is_tar:
            logging.error('You must point tar archive in AWS S3 bucket.')
            exit(-1)
        output = opjoin(PROJECT_DIR, os.path.basename(output))
        s3_bucket_key = create_aws_s3_key(CONFIG['s3']['access_key'],
                                          CONFIG['s3']['secret_key'],
                                          CONFIG['s3']['bucket'], output)

    output_images = opjoin(output_dir, CONFIG['output']['images'])
    output_res_path = opjoin(output_dir, CONFIG['output']['angle'])
    output_gnu_path = opjoin(output_dir, CONFIG['output']['gnuplot'])

    pathbuilder = FilepathBuilder(aei_paths, is_recursive)
    planet_aei_paths = [pathbuilder.build('%s.aei' % x) for x in planets]
    resmaker = ResfileMaker(planets, planet_aei_paths)

    if not os.path.exists(output_images):
        os.makedirs(output_images)

    if not os.path.exists(output_gnu_path):
        os.makedirs(output_gnu_path)

    phase_builder = PhaseBuilder(phase_storage)
    orbital_element_sets = None
    if build_phases:
        orbital_element_sets = build_bigbody_elements(planet_aei_paths)
    phase_loader = PhaseLoader(phase_storage)
    aei_getter = AEIDataGetter(pathbuilder)

    if is_tar:
        tarf = tarfile.open(output, 'w')

    for resonance, aei_data in get_aggregated_resonances(start, stop, for_librations, planets,
                                                         aei_getter, integers):
        if build_phases:
            orbital_elem_set_facade = ResonanceOrbitalElementSetFacade(
                orbital_element_sets, resonance)
            phase_builder.build(aei_data, resonance.id, orbital_elem_set_facade)
        phases = phase_loader.load(resonance.id)
        apocentric_phases = [cutoff_angle(x + pi) for x in phases]
        res_filepath = opjoin(output_res_path, 'A%i_%i.res' %
                              (resonance.asteroid_number, resonance.id))
        gnu_filepath = opjoin(output_gnu_path, 'A%i_%i.gnu' %
                              (resonance.asteroid_number, resonance.id))

        title = 'Asteroid %i %s %s' % (resonance.asteroid_number, str(resonance), ' '.join(planets))
        resmaker.make(phases, aei_data, res_filepath)
        png_path = opjoin(PROJECT_DIR, output_images, 'A%i-res%i%s.png' % (
            resonance.asteroid_number, resonance.id, ''))
        make_plot(res_filepath, gnu_filepath, png_path, title)
        if is_tar:
            tarf.add(png_path, arcname=os.path.basename(png_path))

        resmaker.make(apocentric_phases, aei_data, res_filepath)
        png_path = opjoin(PROJECT_DIR, output_images, 'A%i-res%i%s.png' % (
            resonance.asteroid_number, resonance.id, '-apocentric'))
        make_plot(res_filepath, gnu_filepath, png_path, title)
        if is_tar:
            tarf.add(png_path, arcname=os.path.basename(png_path))

    if is_tar:
        tarf.close()
        shutil.rmtree(output_dir, True)

    if is_s3:
        s3_bucket_key.set_contents_from_filename(output)


class ResfileMaker:
    def __init__(self, planets: Tuple[str], planet_paths: List = None):
        if not planet_paths:
            planet_paths = [opjoin(MERCURY_DIR, '%s.aei' % x) for x in planets]
        self.orbital_element_sets = build_bigbody_elements(planet_paths)

    def make(self, with_phases: List[float], by_aei_data: List[str], filepath: str):
        orbital_elem_set = ComputedOrbitalElementSetFacade(self.orbital_element_sets, with_phases)
        orbital_elem_set.write_to_resfile(filepath, by_aei_data)