import logging
from boto.s3.key import Key
from resonances.entities import ResonanceMixin
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
from resonances.datamining.orbitalelements import FilepathBuilder
from resonances.shortcuts import create_aws_s3_key
from resonances.shortcuts import cutoff_angle
from resonances.shortcuts import is_s3 as _is_s3
from resonances.shortcuts import is_tar as _is_tar
from resonances.datamining import get_resonances_by_asteroids

from resonances.settings import Config
from resonances.view import make_plot

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])


class ResfileMaker:
    def __init__(self, planets: Tuple[str], planet_paths: List = None):
        if not planet_paths:
            planet_paths = [opjoin(MERCURY_DIR, '%s.aei' % x) for x in planets]
        self.orbital_element_sets = build_bigbody_elements(planet_paths)

    def make(self, with_phases: List[float], by_aei_data: List[str], filepath: str):
        orbital_elem_set = ComputedOrbitalElementSetFacade(self.orbital_element_sets, with_phases)
        orbital_elem_set.write_to_resfile(filepath, by_aei_data)


class OutPaths:
    def __init__(self, output_dir: str):
        outoption = CONFIG['output']
        self.output_dir = output_dir
        self.output_images = opjoin(output_dir, outoption['images'])
        self.output_res_path = opjoin(output_dir, outoption['angle'])
        self.output_gnu_path = opjoin(output_dir, outoption['gnuplot'])

        if not os.path.exists(self.output_images):
            os.makedirs(self.output_images)

        if not os.path.exists(self.output_gnu_path):
            os.makedirs(self.output_gnu_path)


class OutTarException(Exception):
    pass


class PlotSaver:
    def __init__(self, out_paths: OutPaths, tarpath: str = None, s3_bucket_key: str = None):
        self.out_paths = out_paths
        self._s3_bucket_key = s3_bucket_key
        self._tarpath = tarpath
        self._tarf = None

    @property
    def tarf(self) -> tarfile.TarFile:
        if not self._tarf:
            if not self._tarpath:
                raise OutTarException()
            self._tarf = tarfile.open(self._tarpath, 'w')
        return self._tarf

    def save(self, png_path):
        if self._tarpath:
            self.tarf.add(png_path, arcname=os.path.basename(png_path))
            return True
        return False

    def __del__(self):
        if self._tarpath is not None:
            self.tarf.close()

        if self._s3_bucket_key:
            self._s3_bucket_key.set_contents_from_filename(self._tarpath)


class ImageBuilder:
    def __init__(self, resonance: ResonanceMixin, title: str, resmaker: ResfileMaker,
                 aei_data: List[str], out_paths: OutPaths):

        self._resonance = resonance
        self._res_filepath = opjoin(out_paths.output_res_path, 'A%i_%i.res' %
                                    (resonance.asteroid_number, resonance.id))
        self._gnu_filepath = opjoin(out_paths.output_gnu_path, 'A%i_%i.gnu' %
                                    (resonance.asteroid_number, resonance.id))
        self._title = title
        self._resmaker = resmaker
        self._out_paths = out_paths
        self._aei_data = aei_data

    def build(self, phases: List[float], suffix: str = '') -> str:
        """makes png and return path to it."""
        output_images = self._out_paths.output_images
        self._resmaker.make(phases, self._aei_data, self._res_filepath)
        png_path = opjoin(PROJECT_DIR, output_images, 'A%i-res%i%s.png' % (
            self._resonance.asteroid_number, self._resonance.id, suffix))
        make_plot(self._res_filepath, self._gnu_filepath, png_path, self._title)

        return png_path


class PlotBuilder:
    def __init__(self, phase_loader: PhaseLoader, saver: PlotSaver,
                 resmaker: ResfileMaker, planets: tuple):
        """Process data and build plots.

        :is_tar: TODO
        :phase_loader: TODO
        :resmaker: TODO

        """
        self._phase_loader = phase_loader
        self._resmaker = resmaker
        self._planets = planets
        self._saver = saver

    def build(self, resonance: ResonanceMixin, aei_data: List[str]):
        phases = self._phase_loader.load(resonance.id)
        apocentric_phases = [cutoff_angle(x + pi) for x in phases]
        title = 'Asteroid %i %s %s' % (resonance.asteroid_number, str(resonance),
                                       ' '.join(self._planets))
        image_builder = ImageBuilder(resonance, title, self._resmaker, aei_data,
                                     self._saver.out_paths)

        png_path = image_builder.build(phases)
        self._saver.save(png_path)
        png_path = image_builder.build(apocentric_phases, '-apocentric')
        self._saver.save(png_path)


def _get_folder_on_s3(tarpath) -> Key:
    """Makes folder for tar archive on AWS S3 bucket."""
    tar_dir = opjoin(PROJECT_DIR, os.path.basename(tarpath))
    s3_bucket_key = create_aws_s3_key(CONFIG['s3']['access_key'],
                                      CONFIG['s3']['secret_key'],
                                      CONFIG['s3']['bucket'], tar_dir)
    return s3_bucket_key


def plot(asteroids: tuple, phase_storage: PhaseStorage, for_librations: bool,
         integers: List[str], aei_paths: Tuple[str, ...], is_recursive: bool, planets: Tuple[str],
         output: str, build_phases: bool):
    is_s3 = _is_s3(output)
    is_tar = _is_tar(output)
    s3_bucket_key = None

    if is_tar:
        output_dir = opjoin(PROJECT_DIR, '.output')
    else:
        output_dir = output
    out_paths = OutPaths(output_dir)

    s3_bucket_key = None
    if is_s3:
        if not is_tar:
            logging.error('You must point tar archive in AWS S3 bucket.')
            exit(-1)
        s3_bucket_key = _get_folder_on_s3(output)

    pathbuilder = FilepathBuilder(aei_paths, is_recursive)
    planet_aei_paths = [pathbuilder.build('%s.aei' % x) for x in planets]
    resmaker = ResfileMaker(planets, planet_aei_paths)

    phase_builder = PhaseBuilder(phase_storage)
    orbital_element_sets = None
    if build_phases:
        orbital_element_sets = build_bigbody_elements(planet_aei_paths)
    phase_loader = PhaseLoader(phase_storage)
    aei_getter = AEIDataGetter(pathbuilder)

    plot_saver = PlotSaver(out_paths, output if is_tar else None, s3_bucket_key)
    builder = PlotBuilder(phase_loader, plot_saver, resmaker, planets)

    for resonance in get_resonances_by_asteroids(asteroids, for_librations, integers, planets):
        aei_data = aei_getter.get_aei_data(resonance.small_body.name)
        if build_phases:
            orbital_elem_set_facade = ResonanceOrbitalElementSetFacade(
                orbital_element_sets, resonance)
            phase_builder.build(aei_data, resonance.id, orbital_elem_set_facade)

        builder.build(resonance, aei_data)

    if is_tar:
        shutil.rmtree(out_paths.output_dir, True)
