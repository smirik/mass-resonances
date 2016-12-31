"""
Module aims to help with convinient io operations.
"""
import os
import shutil
import tarfile
from os.path import join as opjoin
from glob import iglob
from resonances.settings import Config
from resonances.shortcuts import is_tar as _is_tar
from boto.s3.key import Key

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
INTEGRATOR_PATH = os.path.join(PROJECT_DIR, CONFIG['integrator']['dir'])


def move_aei_files(output_path: str):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    for path in iglob(opjoin(INTEGRATOR_PATH, '*.aei')):
        shutil.move(path, opjoin(output_path, os.path.basename(path)))


def save_aei_files(output_path: str, s3_bucket_key: Key):
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
        move_aei_files(output_path)
