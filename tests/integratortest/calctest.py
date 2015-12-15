import unittest
from unittest import mock
import shutil
import os
from os.path import join as opjoin
from os.path import exists as opexists

from settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


class CalcTestCase(unittest.TestCase):
    BODY_NUMBER = 1
    RESONANT_PHASE = 1.
    OUTPUT_ANGLE_DIR = CONFIG['output']['angle']
    MERCURY_DIR = CONFIG['integrator']['dir']

    def setUp(self):
        pass

    def tearDown(self):
        filepath = opjoin(PROJECT_DIR, self.OUTPUT_ANGLE_DIR,
                          'A%i.res' % self.BODY_NUMBER)
        os.remove(filepath)
        shutil.rmtree(os.path.dirname(opjoin(
            PROJECT_DIR, self.OUTPUT_ANGLE_DIR)))

    @mock.patch('entities.ThreeBodyResonance')
    def test_calc(self, ThreeBodyResonanceMock):
        from integrator import calc
        obj = ThreeBodyResonanceMock()
        obj.get_resonant_phase = mock.MagicMock(return_value=self.RESONANT_PHASE)

        calc(self.BODY_NUMBER, obj)
        filepath = opjoin(PROJECT_DIR, self.OUTPUT_ANGLE_DIR,
                          'A%i.res' % self.BODY_NUMBER)
        self.assertTrue(opexists(filepath))

        aei_path = opjoin(PROJECT_DIR, self.MERCURY_DIR, 'A%i.aei' % self.BODY_NUMBER)
        with open(aei_path) as aeifile:
            for i in range(4):
                next(aeifile)
            with open(filepath) as resfile:
                for resline in resfile:
                    aeiline = aeifile.readline()

                    res_values = [float(x) for x in resline.split()]
                    aei_values = [float(x) for x in aeiline.split()]

                    self.assertEqual(res_values[0], aei_values[0])
                    self.assertEqual(res_values[1], self.RESONANT_PHASE)
                    self.assertEqual(res_values[2], aei_values[3])
