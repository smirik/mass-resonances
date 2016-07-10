from typing import Tuple, List, Iterable

from tarfile import TarFile
from tarfile import TarInfo
from .collection import OrbitalElementSetCollection
from .collection import build_bigbody_elements
from .facades import ComputedOrbitalElementSetFacade
from .facades import ResonanceOrbitalElementSetFacade
from .facades import IOrbitalElementSetFacade
from .facades import ElementCountException
from .facades import PhaseCountException
from .collection import OrbitalElementSet

from os.path import exists as opexists
from os.path import join as opjoin
import glob
from tarfile import is_tarfile
from tarfile import open as taropen
import os
from settings import Config
import shutil
PROJECT_DIR = Config.get_project_dir()


class FilepathException(Exception):
    pass


class FilepathInvalidException(Exception):
    pass


class FilepathBuilder:
    """
    Class builds paths of pointed file names from base paths. It will search name recursive if it is
    needed.
    """

    EXTRACT_PATH = opjoin(PROJECT_DIR, '.from_archives')

    def __init__(self, paths: Iterable, is_recursive=False):
        self._last_tar = None
        self._is_recursive = is_recursive
        self._archives = []
        self._dirs = []
        for path in paths:
            if os.path.isdir(path):
                self._dirs.append(path)
            elif is_tarfile(path):
                self._archives.append(path)
        self._check_paths(paths)
        self._dirs.append(self.EXTRACT_PATH)

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

    def _check_paths(self, paths) -> List[str]:
        invalid_paths = [x for x in paths if x not in (self._archives + self._dirs)]
        if invalid_paths:
            raise FilepathInvalidException('Pointed invalid paths %s. Only tar and folder are '
                                           'supported' % ' '.join(invalid_paths))

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
                    tarfile.extract(taritem, self.EXTRACT_PATH)
                    self._last_tar = tarname
                    return opjoin(self.EXTRACT_PATH, filepath)
        return None

    def __del__(self):
        if opexists(self.EXTRACT_PATH):
            shutil.rmtree(self.EXTRACT_PATH)
