import logging
from typing import List, Tuple, Iterable

from resonances.entities import ResonanceMixin, build_resonance, BodyNumberEnum
from resonances.entities import get_resonance_factory
from resonances.settings import Config
from os.path import join as opjoin

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
SKIP_LINES = CONFIG['catalog']['astdys']['skip']
AXIS_COLUMNS = {BodyNumberEnum.two: 4, BodyNumberEnum.three: 6}
ASTDYS = opjoin(PROJECT_DIR, CONFIG['catalog']['file'])


def find_by_number(number: int, catalog_path:str = ASTDYS) -> List[float]:
    """Find asteroid parameters by number in catalog.

    :param int number: num for search.
    :return: list contains parameters of asteroid.
    """

    try:
        with open(catalog_path, 'r') as f_file:
            for i, line in enumerate(f_file):
                if i < number - 1 + SKIP_LINES:
                    continue

                arr = line.split()[1:]
                arr = [float(x) for x in arr]
                arr[4], arr[5] = arr[5], arr[4]
                return arr
    except FileNotFoundError:
        link = 'http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat'
        logging.error('File from astdys doesn\'t exist try this %s' % link)
        exit(-1)


class PossibleResonanceBuilder:
    def __init__(self, planets: Tuple[str], axis_swing: float = 0.01, catalog_path = ASTDYS):
        self.planets = planets
        self.axis_swing = axis_swing
        self.catalog_path = catalog_path

    def build(self, from_source: Iterable, for_asteroid_num: int) -> List[ResonanceMixin]:
        """
        Builds resonances, that can be for pointed asteroid. Resonance is considering if it's semi major
        axis similar to semi major axis of asteroid from catalog. Them compares with some swing, which
        which pointed in settings.

        :param from_source: iterable data with resonance matrix.
        :param for_asteroid_num: number of asteroid.
        :return: list of resonances.
        """
        res = []
        asteroid_parameters = find_by_number(for_asteroid_num, self.catalog_path)
        asteroid_axis = asteroid_parameters[1]
        for line in from_source:
            line_data = line.split()

            body_count = BodyNumberEnum(len(self.planets) + 1)
            assert (body_count == BodyNumberEnum.three and len(line_data) > 5 or
                    body_count == BodyNumberEnum.two)
            resonant_asteroid_axis = float(line_data[AXIS_COLUMNS[body_count]])
            if abs(resonant_asteroid_axis - asteroid_axis) <= self.axis_swing:
                resonance_factory = get_resonance_factory(
                    self.planets, line_data, for_asteroid_num)
                res.append(build_resonance(resonance_factory))

        return res
