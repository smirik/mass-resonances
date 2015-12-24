import os
from typing import List, Iterable, Dict, Tuple
from math import radians
from math import sqrt

from abc import abstractmethod
from utils.shortcuts import cutoff_angle
from entities import ThreeBodyResonance
from entities.body import LONG
from entities import PERI
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


class _OrbitalElementSet:
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
        :return:
        """
        datas = [float(x) for x in data_string.split()]

        self.time = datas[self._TIME]
        self.p_longitude = radians(datas[self._PERIHELLION_LONGITUDE])
        self.mean_anomaly = radians(datas[self._MEAN_ANOMALY])
        self.semi_axis = datas[self._SEMIMAJOR_AXIS]
        self.eccentricity = datas[self._ECCENTRICITY]
        self.inclination = radians(int(datas[self._INCLINATION]))
        self.node = radians(int(datas[self._NODE]))

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

    def serialize_as_asteroid(self) -> List[float]:
        """Represents data for storing in res file for asteroid.
        :return: list of data for asteroid representation.
        """
        return '%f %f %f %f %f' % (self.semi_axis, self.eccentricity, self.inclination,
                                   self.node, self.p_longitude)

    def serialize_as_planet(self) -> List[float]:
        """Represents data for storing in res file for planet.
        :return: list of data for planet representation.
        """
        return '%f %f' % (self.semi_axis, self.eccentricity)


class BigBodyOrbitalElementSet:
    def __init__(self, filepath):
        self._filepath = filepath
        self._set = self._get_orbital_elements()

    def _get_orbital_elements(self) -> List[_OrbitalElementSet]:
        res = []
        with open(self._filepath) as bodyfile:
            for i, line in enumerate(bodyfile):
                if i < HEADER_LINE_COUNT:
                    continue

                res.append(_OrbitalElementSet(line))
        return res

    @property
    def orbital_elements(self) -> List[_OrbitalElementSet]:
        return self._set


class AbstractOrbitalElementSet(object):
    def __init__(self, secondbody_elements: BigBodyOrbitalElementSet,
                 firstbody_elements: BigBodyOrbitalElementSet):
        assert (len(firstbody_elements.orbital_elements) ==
                len(secondbody_elements.orbital_elements))
        self._firstbody_elements = firstbody_elements
        self._secondbody_elements = secondbody_elements

    def _get_body_orbital_elements(self, aei_data: List[str]) \
            -> Iterable[Dict[str, _OrbitalElementSet]]:
        """Get orbital elements of bodies from data of the .aei file.
        :return:
        """
        for i, line in enumerate(aei_data):
            if i < HEADER_LINE_COUNT:
                continue

            index = i - HEADER_LINE_COUNT
            yield {
                SMALL_BODY: _OrbitalElementSet(line),
                FIRST_BODY: self._firstbody_elements.orbital_elements[index],
                SECOND_BODY: self._secondbody_elements.orbital_elements[index]
            }

    def write_to_resfile(self, res_filepath: str, aei_data: List[str]):
        if not os.path.exists(os.path.dirname(res_filepath)):
            os.makedirs(os.path.dirname(res_filepath))
        with open(res_filepath, 'w') as resonance_file:
            for item in self.get_elements(aei_data):
                resonance_file.write(item)

    @abstractmethod
    def get_elements(self, aei_data: List[str]) -> Iterable[str]:
        pass


class OrbitalElementSet(AbstractOrbitalElementSet):
    def __init__(self, secondbody_elements: BigBodyOrbitalElementSet,
                 firstbody_elements: BigBodyOrbitalElementSet,
                 resonant_phases: List[float]):
        super(OrbitalElementSet, self).__init__(
            secondbody_elements, firstbody_elements)
        assert (len(resonant_phases) == len(secondbody_elements.orbital_elements))
        self._resonant_phases = resonant_phases

    def get_elements(self, aei_data: List[str]) -> Iterable[str]:
        for i, orbital_elements in enumerate(self._get_body_orbital_elements(aei_data)):
            resonant_phase = self._resonant_phases[i]
            resonance_data = "%f %f %s %s %s\n" % (
                orbital_elements[SMALL_BODY].time, resonant_phase,
                orbital_elements[SMALL_BODY].serialize_as_asteroid(),
                orbital_elements[FIRST_BODY].serialize_as_planet(),
                orbital_elements[SECOND_BODY].serialize_as_planet()
            )
            yield resonance_data


class ResonanceOrbitalElementSet(AbstractOrbitalElementSet):
    def __init__(self, secondbody_elements: BigBodyOrbitalElementSet,
                 firstbody_elements: BigBodyOrbitalElementSet,
                 resonance: ThreeBodyResonance):
        """
        :param secondbody_elements:
        :param firstbody_elements:
        :param resonance:
        :return:
        """
        super(ResonanceOrbitalElementSet, self).__init__(
            secondbody_elements, firstbody_elements)
        self._resonance = resonance

    # TODO: separate writing of axis and orbital elements to two files.
    def get_elements(self, aei_data: List[str]) -> Iterable[str]:
        for orbital_elements in self._get_body_orbital_elements(aei_data):
            resonant_phase = self._resonance.compute_resonant_phase(
                {LONG: orbital_elements[FIRST_BODY].m_longitude,
                 PERI: orbital_elements[FIRST_BODY].p_longitude},
                {LONG: orbital_elements[SECOND_BODY].m_longitude,
                 PERI: orbital_elements[SECOND_BODY].p_longitude},
                {LONG: orbital_elements[SMALL_BODY].m_longitude,
                 PERI: orbital_elements[SMALL_BODY].p_longitude}
            )
            resonant_phase = cutoff_angle(resonant_phase)
            resonance_data = "%f %f %s %s %s\n" % (
                orbital_elements[SMALL_BODY].time, resonant_phase,
                orbital_elements[SMALL_BODY].serialize_as_asteroid(),
                orbital_elements[FIRST_BODY].serialize_as_planet(),
                orbital_elements[SECOND_BODY].serialize_as_planet()
            )
            yield resonance_data


def build_bigbody_elements(firstbody_filepath: str, secondbody_filepath: str) \
        -> Tuple[BigBodyOrbitalElementSet, BigBodyOrbitalElementSet]:
    firstbody_elements = BigBodyOrbitalElementSet(firstbody_filepath)
    secondbody_elements = BigBodyOrbitalElementSet(secondbody_filepath)
    return firstbody_elements, secondbody_elements
