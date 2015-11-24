from typing import List, Iterable, Dict

from os.path import join as opjoin
from math import radians
from math import sqrt
import os
from utils.shortcuts import cutoff_angle
from entities import ThreeBodyResonance
from entities import LONG
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


def _get_body_orbital_elements(
        smallbody_filepath: str, firstbody_filepath: str,
        secondbody_filepath: str) -> Iterable[Dict[str, List[float]]]:
    """Get orbital elements of bodies from pointed .aei files.
    :param smallbody_filepath:
    :param firstbody_filepath:
    :param secondbody_filepath:
    :return:
    """

    def _parse_orbital_elements(from_string: str) -> List[float]:
        """Represents data from .aei file as set of parameters, which ready for computings.
        :param from_string: line with parameters.
        :return:
        """

        def _get_mean_motion(from_axis: float) -> float:
            return sqrt(0.0002959122082855911025 / from_axis ** 3.)

        datas = from_string.split()
        time = datas[0]
        p_longitude = radians(float(datas[1]))
        mean_anomaly = radians(float(datas[2]))
        semi_axis = float(datas[3])
        ecc = float(datas[4])
        inclination = radians(int(float(datas[5])))
        node = radians(int(float(datas[7])))

        m_longitude = p_longitude + mean_anomaly
        mean_motion = _get_mean_motion(semi_axis)

        return [time, m_longitude, p_longitude, mean_motion, semi_axis, ecc,
                mean_anomaly, inclination, node]

    smallbody_file = open(smallbody_filepath)
    firstbody_file = open(firstbody_filepath)
    secondbody_file = open(secondbody_filepath)

    for i, line in enumerate(smallbody_file):
        if i < 4:  # skips header.
            next(firstbody_file)
            next(secondbody_file)
            continue

        yield {
            SMALL_BODY: _parse_orbital_elements(line),
            FIRST_BODY: _parse_orbital_elements(firstbody_file.readline()),
            SECOND_BODY: _parse_orbital_elements(secondbody_file.readline())
        }

    smallbody_file.close()
    firstbody_file.close()
    secondbody_file.close()


class ResonanceOrbitalElementSet:
    def __init__(self, resonance: ThreeBodyResonance, firstbody_filepath: str,
                 secondbody_filepath: str):
        self._firstbody_filepath = firstbody_filepath
        self._secondbody_filepath = secondbody_filepath
        self._resonance = resonance

    # TODO: separate writing of axis and orbital elements to two files.
    def get_elements(self, smallbody_filepath: str) -> Iterable[str]:
        for orbitanl_elements in self._get_body_orbital_elements(smallbody_filepath):
            resonant_phase = self._resonance.get_resonant_phase(
                {LONG: orbitanl_elements[FIRST_BODY][1],
                 PERI: orbitanl_elements[FIRST_BODY][2]},
                {LONG: orbitanl_elements[SECOND_BODY][1],
                 PERI: orbitanl_elements[SECOND_BODY][2]},
                {LONG: orbitanl_elements[SMALL_BODY][1],
                 PERI: orbitanl_elements[SMALL_BODY][2]}
            )
            resonant_phase = cutoff_angle(resonant_phase)

            # time, resonance parameter, s/m axis a, ecc a, inclination a,
            # node a, p_longitude a, s/m axis 1, ecc 1, s/m axis 2, ecc 2
            resonance_data = "%s %f %f %f %f %f %f %f %f %f %f\n" % (
                orbitanl_elements[SMALL_BODY][0], resonant_phase,
                orbitanl_elements[SMALL_BODY][4], orbitanl_elements[SMALL_BODY][5],
                orbitanl_elements[SMALL_BODY][7], orbitanl_elements[SMALL_BODY][8],
                orbitanl_elements[SMALL_BODY][2], orbitanl_elements[FIRST_BODY][4],
                orbitanl_elements[FIRST_BODY][5], orbitanl_elements[SECOND_BODY][4],
                orbitanl_elements[SECOND_BODY][5]
            )
            yield resonance_data

    def _get_body_orbital_elements(self, smallbody_filepath: str)\
            -> Iterable[Dict[str, List[float]]]:
        """Get orbital elements of bodies from pointed .aei files.

        :param smallbody_filepath:
        :return:
        """

        def _parse_orbital_elements(from_string: str) -> List[float]:
            """Represents data from .aei file as set of parameters, which ready for computings.
            :param from_string: line with parameters.
            :return:
            """

            def _get_mean_motion(from_axis: float) -> float:
                return sqrt(0.0002959122082855911025 / from_axis ** 3.)

            datas = from_string.split()
            time = datas[0]
            p_longitude = radians(float(datas[1]))
            mean_anomaly = radians(float(datas[2]))
            semi_axis = float(datas[3])
            ecc = float(datas[4])
            inclination = radians(int(float(datas[5])))
            node = radians(int(float(datas[7])))

            m_longitude = p_longitude + mean_anomaly
            mean_motion = _get_mean_motion(semi_axis)

            return [time, m_longitude, p_longitude, mean_motion, semi_axis, ecc,
                    mean_anomaly, inclination, node]

        smallbody_file = open(smallbody_filepath)
        firstbody_file = open(self._firstbody_filepath)
        secondbody_file = open(self._secondbody_filepath)

        for i, line in enumerate(smallbody_file):
            if i < 4:  # skips header.
                next(firstbody_file)
                next(secondbody_file)
                continue

            yield {
                SMALL_BODY: _parse_orbital_elements(line),
                FIRST_BODY: _parse_orbital_elements(firstbody_file.readline()),
                SECOND_BODY: _parse_orbital_elements(secondbody_file.readline())
            }

        smallbody_file.close()
        firstbody_file.close()
        secondbody_file.close()


def calc(body_number: int, resonance: ThreeBodyResonance):
    """Returns path of file, which contains results of calculation.

    :param body_number:
    :param resonance:
    :return:
    """
    project_dir = Config.get_project_dir()

    mercury_dir = opjoin(project_dir, CONFIG['integrator']['dir'])
    mercury_planet_dir = mercury_dir

    body_number_start = body_number - body_number % 100
    body_number_stop = body_number_start + BODIES_COUNTER
    aei_dir = opjoin(
        project_dir, CONFIG['export']['aei_dir'],
        '%i-%i' % (body_number_start, body_number_stop), 'aei'
    )
    aei_filepath = opjoin(aei_dir, 'A%i.aei' % body_number)
    if os.path.exists(aei_filepath):
        mercury_dir = aei_dir
        mercury_planet_dir = opjoin(
            project_dir, CONFIG['export']['aei_dir'], 'Planets'
        )

    resonance_filename = opjoin(project_dir, OUTPUT_ANGLE, 'A%i.res' % body_number)
    bodies_filenames = [
        opjoin(mercury_dir, 'A%i.aei' % body_number),
        opjoin(mercury_planet_dir, '%s.aei' % BODY1),
        opjoin(mercury_planet_dir, '%s.aei' % BODY2),
    ]

    dirpath = opjoin(project_dir, OUTPUT_ANGLE)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    with open(resonance_filename, 'w+') as resonance_file:
        for orbitanl_elements in _get_body_orbital_elements(*bodies_filenames):
            resonant_phase = resonance.get_resonant_phase(
                {LONG: orbitanl_elements[FIRST_BODY][1],
                 PERI: orbitanl_elements[FIRST_BODY][2]},
                {LONG: orbitanl_elements[SECOND_BODY][1],
                 PERI: orbitanl_elements[SECOND_BODY][2]},
                {LONG: orbitanl_elements[SMALL_BODY][1],
                 PERI: orbitanl_elements[SMALL_BODY][2]}
            )
            resonant_phase = cutoff_angle(resonant_phase)

            # time, resonance parameter, s/m axis a, ecc a, inclination a,
            # node a, p_longitude a, s/m axis 1, ecc 1, s/m axis 2, ecc 2
            resonance_data = "%s %f %f %f %f %f %f %f %f %f %f\n" % (
                orbitanl_elements[SMALL_BODY][0], resonant_phase,
                orbitanl_elements[SMALL_BODY][4], orbitanl_elements[SMALL_BODY][5],
                orbitanl_elements[SMALL_BODY][7], orbitanl_elements[SMALL_BODY][8],
                orbitanl_elements[SMALL_BODY][2], orbitanl_elements[FIRST_BODY][4],
                orbitanl_elements[FIRST_BODY][5], orbitanl_elements[SECOND_BODY][4],
                orbitanl_elements[SECOND_BODY][5]
            )
            resonance_file.write(resonance_data)

    return resonance_filename
