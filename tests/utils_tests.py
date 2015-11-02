import unittest
from os.path import join as opjoin
from os.path import exists as opexists
import os

from settings import ConfigSingleton
import settings
from utils.series import get_max_diff
from utils import ResonanceDatabase

setattr(settings, 'PROJECT_DIR', opjoin(settings.PROJECT_DIR, 'tests'))
CONFIG = ConfigSingleton.get_singleton()


class SeriesTestCase(unittest.TestCase):
    def test_get_max_diff(self):
        data = [10000, 12000, 14000, 90000, 100000]
        res = get_max_diff(data)
        self.assertEqual(res, 76000)


class ResonanceDatabaseTestCase(unittest.TestCase):
    def test_init(self):
        def _common_test(path: str=None):
            if not path:
                path = opjoin(settings.PROJECT_DIR,
                              CONFIG['resonance']['db_file'])

            obj = ResonanceDatabase(path)
            self.assertEqual(obj.db_file, path)
            self.assertTrue(opexists(obj.db_file))
            os.remove(path)
            os.removedirs(os.path.dirname(path))

        def _test_custom_path_db():
            _common_test(opjoin(
                settings.PROJECT_DIR, 'export', 'unittest_db.txt'
            ))

        def _test_default_path_db():
            _common_test()

        _test_custom_path_db()
        _test_default_path_db()
