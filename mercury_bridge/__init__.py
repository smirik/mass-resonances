from typing import List
from math import radians
from math import sqrt
import os
from os.path import join as opjoin
from settings import ConfigSingleton
from settings import PROJECT_DIR
from utils.shortcuts import cutoff_angle

CONFIG = ConfigSingleton.get_singleton()
BODY1 = CONFIG['resonance']['bodies'][0]
BODY2 = CONFIG['resonance']['bodies'][1]
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
OUTPUT_ANGLE = CONFIG['output']['angle']


def add_small_body(number: int, elements: List[float]):
    """Write to file, which contains data of asteroids.

    :param int number: number of asteroid
    :param list elements: parameters
    :raises: FileNotFoundError
    :raises: IndexError
    """
    ep = CONFIG['integrator']['start']
    input_dir = opjoin(PROJECT_DIR, CONFIG['integrator']['input'])
    path = opjoin(
        input_dir, CONFIG['integrator']['files']['small_bodies']
    )

    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    try:
        with open(path, 'a+') as fd:
            fd.write(' A%i ep=%s\n' % (number, ep))
            fd.write(' %s 0 0 0\n' % ' '.join([str(x) for x in elements[1:7]]))
    except FileNotFoundError as e:
        raise e
    except IndexError as e:
        raise e


def calc(body_number: int, resonance: List[float]):
    def _parse_elements(from_string: str) -> List[float]:
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

    mercury_dir = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])
    mercury_planet_dir = mercury_dir

    body_number_start = body_number - body_number % 100
    body_number_stop = body_number_start + BODIES_COUNTER
    aei_dir = opjoin(
        PROJECT_DIR, CONFIG['export']['aei_dir'],
        '%i-%i' % (body_number_start, body_number_stop), 'aei'
    )
    aei_filpath = opjoin(aei_dir, 'A%i.aei' % body_number)
    if os.path.exists(aei_filpath):
        mercury_dir = aei_dir
        mercury_planet_dir = opjoin(
            PROJECT_DIR, CONFIG['export']['aei_dir'], 'Planets'
        )

    result_filename = opjoin(PROJECT_DIR, OUTPUT_ANGLE, 'A%i.res' % body_number)

    bodies_filename = [
        opjoin(mercury_dir, 'A%i.aei' % body_number),
        opjoin(mercury_planet_dir, '%s.aei' % BODY1),
        opjoin(mercury_planet_dir, '%s.aei' % BODY2),
    ]

    # Open 3 files
    bodies_files = []
    for value in bodies_filename:
        bodies_files.append(open(value))

    content = [[], [], []]

    # Load 3 files into 3-dimensional array
    for i in range(3):
        for line in bodies_files[i]:
            content[i].append(line)

    dirpath = opjoin(PROJECT_DIR, OUTPUT_ANGLE)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    with open(result_filename, 'w+') as result_file:
        for i in range(4, len(content[0])):
            data = []
            for j in range(3):
                data.append(_parse_elements(content[j][i]))
            angle = (resonance[0] * data[1][1] +
                     resonance[1] * data[2][1] +
                     resonance[2] * data[0][1] +
                     resonance[3] * data[1][2] +
                     resonance[4] * data[2][2] +
                     resonance[5] * data[0][2])
            angle = cutoff_angle(angle)

            # time, resonance parameter, s/m axis a, ecc a, inclination a, node a, p_longitude a, s/m axis 1, ecc 1, s/m axis 2, ecc 2
            ss = "%s %f %f %f %f %f %f %f %f %f %f\n" % (
                data[0][0], angle, data[0][4], data[0][5], data[0][7],
                data[0][8], data[0][2], data[1][4], data[1][5], data[2][4],
                data[2][5])
            result_file.write(ss)

    for file in bodies_files:
        file.close()


def create_small_body_file():
    header = ")O+_06 Small-body initial data  (WARNING: Do not delete this line!!)\n" \
             ") Lines beginning with `)' are ignored.\n" \
             ")---------------------------------------------------------------------\n" \
             " style (Cartesian, Asteroidal, Cometary) = Ast" \
             "\n)---------------------------------------------------------------------\n"
    filename = opjoin(
        PROJECT_DIR,
        CONFIG['integrator']['input'],
        CONFIG['integrator']['files']['small_bodies']
    )
    fd = open(filename, 'w')
    fd.write(header)
    fd.close()
