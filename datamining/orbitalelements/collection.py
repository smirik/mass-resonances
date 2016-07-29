from math import radians
from math import sqrt
from typing import List, Tuple

from settings import Config

SMALL_BODY = 'small_body'
CONFIG = Config.get_params()
OUTPUT_ANGLE = CONFIG['output']['angle']
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
SMALL_BODIES_FILENAME = CONFIG['integrator']['files']['small_bodies']
HEADER_LINE_COUNT = 4


class AEIValueError(ValueError):
    pass


class OrbitalElementSet:
    _TIME = 0
    _PERIHELLION_LONGITUDE = 1
    _MEAN_ANOMALY = 2
    _SEMIMAJOR_AXIS = 3
    _ECCENTRICITY = 4
    _INCLINATION = 5
    _NODE = 7

    def __init__(self, data_string: str):
        """Data string must be formated as data in aei file, that generates by element6.
        :param data_string:
        :except ValueError: if data from data_string has incorrect values.
        :return:
        """
        try:
            self._datas = [x for x in data_string.split()]
            self.time = float(self._datas[self._TIME])
            self.p_longitude = radians(float(self._datas[self._PERIHELLION_LONGITUDE]))
            self.mean_anomaly = radians(float(self._datas[self._MEAN_ANOMALY]))
            self._semi_axis = None
            self._eccentricity = None
            self._inclination = None
            self._node = None
        except ValueError:
            raise AEIValueError()

    @property
    def node(self) -> float:
        if not self._node:
            self._node = radians(int(float(self._datas[self._NODE])))
        return self._node

    @property
    def inclination(self) -> float:
        if not self._inclination:
            self._inclination = radians(int(float(self._datas[self._INCLINATION])))
        return self._inclination

    @property
    def eccentricity(self) -> float:
        if not self._eccentricity:
            self._eccentricity = float(self._datas[self._ECCENTRICITY])
        return self._eccentricity

    @property
    def semi_axis(self) -> float:
        if not self._semi_axis:
            self._semi_axis = float(self._datas[self._SEMIMAJOR_AXIS])
        return self._semi_axis

    @property
    def m_longitude(self) -> float:
        """Computes and returns longitude by perihelion longitude.
        :return: longitude
        """
        return self.p_longitude + self.mean_anomaly

    @property
    def mean_motion(self) -> float:
        """Gets mean motion.
        :return: mean motion
        """
        return sqrt(0.0002959122082855911025 / self.semi_axis ** 3.)

    def serialize_as_asteroid(self) -> str:
        """Represents data for storing in res file for asteroid.
        :return: list of data for asteroid representation.
        """
        return '%f %f %f %f %f' % (self.semi_axis, self.eccentricity, self.inclination,
                                   self.node, self.p_longitude)

    def serialize_as_planet(self) -> str:
        """Represents data for storing in res file for planet.
        :return: list of data for planet representation.
        """
        return '%f %f' % (self.semi_axis, self.eccentricity)


class OrbitalElementSetCollection:
    """Class represents set of orbital elements for planet.
    """
    def __init__(self, filepath: str):
        """Caches aei data to internal field _set.
        :param filepath: path to aei file, that stores data about orbital elements.
        """
        self._filepath = filepath
        self._set = self._get_orbital_elements()

    def _get_orbital_elements(self) -> List[OrbitalElementSet]:
        res = []
        with open(self._filepath) as bodyfile:
            for i, line in enumerate(bodyfile):
                if i < HEADER_LINE_COUNT:
                    continue

                res.append(OrbitalElementSet(line))
        return res

    @property
    def orbital_elements(self) -> List[OrbitalElementSet]:
        """
        :return: list of orbital elements, that stored in aei file earlier.
        """
        return self._set

    def __getitem__(self, item: int) -> OrbitalElementSet:
        return self.orbital_elements[item]

    def __len__(self) -> int:
        return len(self.orbital_elements)


def build_bigbody_elements(planet_filepaths: List[str]) -> List[OrbitalElementSetCollection]:
    res = []
    for filepath in planet_filepaths:
        res.append(OrbitalElementSetCollection(filepath))
    return res
