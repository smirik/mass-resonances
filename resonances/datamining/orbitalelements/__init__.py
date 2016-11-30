import glob
import os
import shutil
from os import makedirs
from os.path import basename
from os.path import exists as opexists
from os.path import isabs
from os.path import join as opjoin
from tarfile import TarFile
from tarfile import TarInfo
from tarfile import is_tarfile
from tarfile import open as taropen
from typing import Iterable
from typing import List

from boto.s3.connection import S3Connection
from resonances.shortcuts import is_s3

from resonances.settings import Config
from .collection import OrbitalElementSet
from .collection import OrbitalElementSetCollection
from .collection import build_bigbody_elements
from .facades import ComputedOrbitalElementSetFacade
from .facades import ElementCountException
from .facades import IOrbitalElementSetFacade
from .facades import PhaseCountException
from .facades import ResonanceOrbitalElementSetFacade

PROJECT_DIR = Config.get_project_dir()
CONFIG = Config.get_params()
_ex_folder = CONFIG['extract_dir']
EXTRACT_PATH = _ex_folder if isabs(_ex_folder) else opjoin(PROJECT_DIR, _ex_folder)

BUCKET = CONFIG['s3']['bucket']
_s3_folder = CONFIG['s3files_dir']
S3_FILES_DIR = _s3_folder if isabs(_s3_folder) else opjoin(PROJECT_DIR, _s3_folder)


class FilepathException(Exception):
    pass


class FilepathInvalidException(Exception):
    pass


def _get_from_s3(filepaths: List[str]) -> List[str]:
    new_paths = []
    if any([is_s3(x) for x in filepaths]):
        conn = S3Connection(CONFIG['s3']['access_key'], CONFIG['s3']['secret_key'])
        bucket = conn.get_bucket(BUCKET)
        for path in filepaths:
            if not is_s3(path):
                continue
            start = path.index(BUCKET)
            filename = path[start + len(BUCKET) + 1:]
            if not opexists(S3_FILES_DIR):
                makedirs(S3_FILES_DIR)
            local_path = opjoin(S3_FILES_DIR, basename(filename))
            if not opexists(local_path):
                s3key = bucket.get_key(filename, validate=False)
                with open(local_path, 'wb') as f:
                    s3key.get_contents_to_file(f)
                if not is_tarfile(local_path):
                    raise FilepathInvalidException('%s is not tar. Local copy %s' %
                                                   (path, local_path))
            new_paths.append(local_path)
    return new_paths


def _check(paths, by_controlling: List[str]) -> List[str]:
    invalid_paths = [x for x in paths if x not in by_controlling]
    if invalid_paths:
        raise FilepathInvalidException('Pointed invalid paths %s. Only tar and folder are '
                                       'supported' % ' '.join(invalid_paths))


class FilepathBuilder:
    """
    Class builds paths of pointed file names from base paths. It will search name recursive if it is
    needed.
    """

    def __init__(self, paths: Iterable, is_recursive=False, is_clear_downloaded: bool = False):
        self._is_clear_downloaded = is_clear_downloaded
        self._last_tar = None
        self._is_recursive = is_recursive
        self._archives = []
        self._dirs = []
        s3paths = []

        for path in paths:
            if is_s3(path):
                s3paths.append(path)
            elif os.path.isdir(path):
                self._dirs.append(path)
            elif is_tarfile(path):
                self._archives.append(path)

        _check(paths, self._dirs + self._archives + s3paths)
        self._archives += _get_from_s3(s3paths)
        self._dirs.append(EXTRACT_PATH)

    def build(self, for_name: str) -> str:
        """ Builds full path by pointed filename.
        :param for_name: pointed filename.
        :return:
        """
        res = self._build_from_dirs(for_name)
        if res:
            return res

        res = self._build_from_tars(for_name)
        if res:
            return res

        raise FilepathException('File %s doesn\'t exist in folders %s' %
                                (for_name, ', '.join(self._dirs + self._archives)))

    def _build_from_dirs(self, for_name: str) -> str:
        res = None
        if self._is_recursive:
            for path_base in self._dirs:
                for filepath in glob.iglob(opjoin(path_base, '**', for_name), recursive=True):
                    res = filepath
                    break
        else:
            for path_base in self._dirs:
                filepath = opjoin(path_base, for_name)
                if opexists(filepath):
                    res = filepath

        return res

    def _build_from_tars(self, for_name: str) -> str:
        archives = [self._last_tar] + self._archives if self._last_tar else self._archives
        for tarname in archives:
            with taropen(tarname) as tarfile:  # type: TarFile
                for taritem in tarfile:  # type: TarInfo
                    filepath = taritem.name
                    if for_name not in filepath:
                        continue
                    tarfile.extract(taritem, EXTRACT_PATH)
                    self._last_tar = tarname
                    return opjoin(EXTRACT_PATH, filepath)
        return None

    def __del__(self):
        if opexists(EXTRACT_PATH):
            shutil.rmtree(EXTRACT_PATH)

        if self._is_clear_downloaded and opexists(S3_FILES_DIR):
            shutil.rmtree(S3_FILES_DIR)

