from typing import List, Tuple
import pytest
from catalog import find_by_number
from settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


@pytest.mark.parametrize('number, catalog_values',
                         [(1, [57400.0, 2.7681116175738203, 0.07575438197786899, 10.59165825139208,
                               72.73329603027756, 80.32179293568826, 181.38128433921716, 3.41,
                               0.12]),
                          (2, [57400.0, 2.772362122525498, 0.2310236014408419, 34.84094939488245,
                               309.98944656158335, 173.0882797978601, 163.60442273654294, 4.09,
                               0.11])])
def test_find_by_number(number: int, catalog_values: List[float]):
    assert find_by_number(number) == catalog_values

