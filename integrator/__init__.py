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
SMALL_BODIES_FILENAME = CONFIG['integrator']['files']['small_bodies']
INTEGRATOR_START = CONFIG['integrator']['start']


def calc(body_number: int, resonance: List[float]):
    """

    :param body_number:
    :param resonance:
    :return:
    """
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
    aei_filepath = opjoin(aei_dir, 'A%i.aei' % body_number)
    if os.path.exists(aei_filepath):
        mercury_dir = aei_dir
        mercury_planet_dir = opjoin(
            PROJECT_DIR, CONFIG['export']['aei_dir'], 'Planets'
        )

    resonance_filename = opjoin(PROJECT_DIR, OUTPUT_ANGLE, 'A%i.res' % body_number)

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

    with open(resonance_filename, 'w+') as resonance_file:
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

            # time, resonance parameter, s/m axis a, ecc a, inclination a,
            # node a, p_longitude a, s/m axis 1, ecc 1, s/m axis 2, ecc 2
            resonance_data = "%s %f %f %f %f %f %f %f %f %f %f\n" % (
                data[0][0], angle, data[0][4], data[0][5], data[0][7],
                data[0][8], data[0][2], data[1][4], data[1][5], data[2][4],
                data[2][5])
            resonance_file.write(resonance_data)

    for file in bodies_files:
        file.close()


class SmallBodiesFileBuilder(object):
    """Builder of file, which contains integration data of small bodies for
    mercury6.
    """
    HEADER = ")O+_06 Small-body initial data  (WARNING: Do not delete this line!!)\n" \
             ") Lines beginning with `)' are ignored.\n" \
             ")---------------------------------------------------------------------\n" \
             " style (Cartesian, Asteroidal, Cometary) = Ast" \
             "\n)---------------------------------------------------------------------\n"

    def __init__(self, filepath: str, symlink: str = None):
        """
        :param filepath: path to file, where will be stored small sky bodies.
        :param symlink: path to symlink of file, pointed by filepath.
        :return:
        """
        self._symlink_path = symlink
        self._filepath = filepath
        self._bodies = []

    def create_small_body_file(self):
        """Creates file by pointed path and adds header to it. If path of
        symlink has been pointed. This method creates symlink by pointed path.
        """
        if not os.path.exists(os.path.dirname(self._filepath)):
            os.makedirs(os.path.dirname(self._filepath))

        with open(self._filepath, 'w') as integrator_file:
            integrator_file.write(self.HEADER)

        if self._symlink_path:
            if os.path.exists(self._symlink_path):
                os.remove(self._symlink_path)
            os.symlink(self._filepath, self._symlink_path)

    def add_body(self, number: int, elements: List[float]):
        """Write to file, which contains data of asteroids.

        :param int number: number of asteroid.
        :param list elements: parameters.
        """
        self._bodies.append({
            'number': number,
            'elements': elements[1:7]
        })

    def flush(self):
        """Writes all bodies data to pointed file and clear from object.
        :raises: FileNotFoundError if file doesn't exist
        :return:
        """
        if not os.path.exists(self._filepath):
            raise FileNotFoundError
        with open(self._filepath, 'a+') as integrator_file:
            for body in self._bodies:
                integrator_file.write(' A%i ep=%s\n' % (body['number'],
                                                        INTEGRATOR_START))
                integrator_file.write(' %s 0 0 0\n' % ' '.join(
                    [str(x) for x in body['elements']]))
            self._bodies.clear()

