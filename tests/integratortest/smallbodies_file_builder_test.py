import unittest
from os.path import join as opjoin
from os.path import exists as opexists
import os
from settings import Config


CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


class SmallBodiesFileBuilderTestCase(unittest.TestCase):
    FILEPATH = opjoin(PROJECT_DIR, 'small.in')
    SYMLINK = opjoin(PROJECT_DIR, 'small.in.link')

    def tearDown(self):
        if opexists(self.FILEPATH):
            os.remove(self.FILEPATH)

    def test_create_small_body_file(self):
        from integrator import SmallBodiesFileBuilder

        def _test_with_symlink():
            builder = SmallBodiesFileBuilder(self.FILEPATH, self.SYMLINK)
            builder.create_small_body_file()

            self.assertTrue(opexists(self.FILEPATH))
            self.assertTrue(opexists(self.SYMLINK))

            os.remove(self.FILEPATH)
            os.remove(self.SYMLINK)

        def _test_without_symlink():
            builder = SmallBodiesFileBuilder(self.FILEPATH)
            builder.create_small_body_file()

            self.assertTrue(opexists(self.FILEPATH))
            self.assertFalse(opexists(self.SYMLINK))

            os.remove(self.FILEPATH)

        _test_with_symlink()
        _test_without_symlink()

    def test_flush(self):
        from integrator import SmallBodiesFileBuilder

        def _test_file_existance():
            builder = SmallBodiesFileBuilder(self.FILEPATH)
            builder.add_body(1, [1., 2., 3., 4., 5., 6., 7.])
            with self.assertRaises(FileNotFoundError):
                builder.flush()

        def _test_success_flush():
            builder = SmallBodiesFileBuilder(self.FILEPATH)
            builder.create_small_body_file()
            builder.add_body(1, [1., 2., 3., 4., 5., 6., 7.])
            builder.flush()

            with open(self.FILEPATH) as f:
                total_lines_count = sum(1 for _ in f)
                self.assertEqual(total_lines_count, 7)

            os.remove(self.FILEPATH)

        _test_file_existance()
        _test_success_flush()
