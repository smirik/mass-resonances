import unittest
from utils.series import get_max_diff


class SeriesTestCase(unittest.TestCase):
    def test_get_max_diff(self):
        data = [10000, 12000, 14000, 90000, 100000]
        res = get_max_diff(data)
        self.assertEqual(res, 76000)
