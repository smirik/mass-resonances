from math import radians
from math import sqrt
from typing import List, Tuple

from settings import Config

SMALL_BODY = 'small_body'
FIRST_BODY = 'first_body'
SECOND_BODY = 'second_body'
CONFIG = Config.get_params()
OUTPUT_ANGLE = CONFIG['output']['angle']
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
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
            datas = [float(x) for x in data_string.split()]
            self.time = datas[self._TIME]
            self.p_longitude = radians(datas[self._PERIHELLION_LONGITUDE])
            self.mean_anomaly = radians(datas[self._MEAN_ANOMALY])
            self.semi_axis = datas[self._SEMIMAJOR_AXIS]
            self.eccentricity = datas[self._ECCENTRICITY]
            self.inclination = radians(int(datas[self._INCLINATION]))
            self.node = radians(int(datas[self._NODE]))
        except ValueError:
            raise AEIValueError()

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


def build_bigbody_elements(firstbody_filepath: str, secondbody_filepath: str) \
        -> Tuple[OrbitalElementSetCollection, OrbitalElementSetCollection]:
    firstbody_elements = OrbitalElementSetCollection(firstbody_filepath)
    secondbody_elements = OrbitalElementSetCollection(secondbody_filepath)
    return firstbody_elements, secondbody_elements
