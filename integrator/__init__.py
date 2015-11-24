from typing import List

import os
from settings import Config
from .calc import calc
from .calc import ResonanceOrbitalElementSet

CONFIG = Config.get_params()
INTEGRATOR_START = CONFIG['integrator']['start']


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
