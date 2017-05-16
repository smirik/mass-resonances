from typing import Iterable
import logging
import os

from resonances.integrator import SmallBodiesFileBuilder, set_time_interval
from resonances.integrator import aei_clean
from resonances.integrator import element6
from resonances.integrator import mercury6
from resonances.integrator import simple_clean
from resonances.shortcuts import create_aws_s3_key
from resonances.shortcuts import is_tar as _is_tar
from resonances.shortcuts import is_s3 as _is_s3
from resonances.io import save_aei_files
from resonances.catalog import AsteroidData

from resonances.settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
SMALL_BODIES_FILENAME = CONFIG['integrator']['files']['small_bodies']
INTEGRATOR_PATH = os.path.join(PROJECT_DIR, CONFIG['integrator']['dir'])


class MercuryException(Exception):
    pass


def _execute_mercury():
    """Execute mercury program

    :raises FileNotFoundError: if mercury not installed.
    """
    try:
        simple_clean(False)
        code = mercury6()
        code += element6()
        if code:
            raise MercuryException('Mercury6 programms has been finished with errors.')

    except FileNotFoundError as e:
        raise e


def number_gen(start: int, stop: int, step: int):
    for i in range(start, stop, step):
        end = i + step if i + step < stop else stop
        yield i, end


def calc(buffered_asteroid_names: Iterable[AsteroidData], from_day: float, to_day: float,
         output_path: str = INTEGRATOR_PATH):
    """
    :param from_day:
    :param to_day:
    :param int start: start is position of start element for computing.
    :param int stop:
    :param str output_path: path where will be saved aei files.
    """
    set_time_interval(from_day, to_day)
    aei_clean()
    is_s3 = _is_s3(output_path)
    s3_bucket_key = None
    if is_s3:
        if not _is_tar(output_path):
            logging.error('You must point tar.gz archive in AWS S3 bucket.')
        s3_bucket_key = create_aws_s3_key(CONFIG['s3']['access_key'],
                                          CONFIG['s3']['secret_key'],
                                          CONFIG['s3']['bucket'], output_path)

    for asteroid_names in buffered_asteroid_names:
        _integrate(asteroid_names)

    save_aei_files(output_path, s3_bucket_key)


def _integrate(asteroid_data: AsteroidData):
    """Gets from astdys catalog parameters of orbital elements. Represents them
    to small.in file and makes symlink of this file in directory of application
    mercury6.

    :param int start: start is position of start element for computing.
    :param int stop:
    """
    filepath = os.path.join(PROJECT_DIR, CONFIG['integrator']['input'], SMALL_BODIES_FILENAME)
    symlink = os.path.join(INTEGRATOR_PATH, SMALL_BODIES_FILENAME)
    small_bodies_storage = SmallBodiesFileBuilder(filepath, symlink)
    small_bodies_storage.create_small_body_file()
    logging.info('Create initial conditions for asteroids from %s to %s',
                 asteroid_data[0][0], asteroid_data[-1][0])

    for name, data in asteroid_data:
        small_bodies_storage.add_body(name, data)
    small_bodies_storage.flush()

    logging.info('Integrating orbits...')
    _execute_mercury()
    logging.info('[done]')
