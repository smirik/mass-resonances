import logging
import os
import tarfile
from glob import iglob
from os.path import join as opjoin

from boto.s3.key import Key
from resonances.integrator import SmallBodiesFileBuilder, set_time_interval
from resonances.integrator import aei_clean
from resonances.integrator import element6
from resonances.integrator import mercury6
from resonances.integrator import simple_clean
from resonances.shortcuts import create_aws_s3_key
from resonances.shortcuts import is_tar as _is_tar
from resonances.shortcuts import is_tar as _is_s3

from resonances.catalog import find_by_number
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


def calc(start: int, stop: int, step: int, from_day: float, to_day: float,
         output_path: str = INTEGRATOR_PATH):
    """
    :param from_day:
    :param to_day:
    :param int start: start is position of start element for computing.
    :param int stop:
    :param str target_path: path where will be saved aei files.
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

    for i in range(start, stop, step):
        end = i + step if i + step < stop else stop
        _integrate(i, end)

    _save_aei_files(output_path, s3_bucket_key)


def _save_aei_files(output_path: str, s3_bucket_key: Key):
    if INTEGRATOR_PATH == output_path:
        return
    if _is_tar(output_path):
        tar_path = output_path
        if s3_bucket_key:
            tar_path = opjoin(PROJECT_DIR, os.path.basename(output_path))

        with tarfile.open(tar_path, 'w:gz') as tarf:
            for path in iglob(os.path.join(INTEGRATOR_PATH, '*.aei')):
                tarf.add(path, arcname=os.path.basename(path))
                os.remove(path)

        if s3_bucket_key:
            s3_bucket_key.set_contents_from_filename(tar_path)
    else:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for path in iglob(os.path.join(INTEGRATOR_PATH, '*.aei')):
            os.rename(path, os.path.join(output_path, os.path.basename(path)))


def _integrate(start: int, stop: int):
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
    logging.info('Create initial conditions for asteroids from %i to %i', start, stop)

    for i in range(start, stop):
        arr = find_by_number(i)
        small_bodies_storage.add_body(i, arr)
    small_bodies_storage.flush()

    logging.info('Integrating orbits...')
    _execute_mercury()
    logging.info('[done]')
