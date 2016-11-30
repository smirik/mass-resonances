import os
from os.path import join as opjoin
from typing import List, Callable, TextIO, Iterable

from resonances.settings import Config

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


def set_time_interval(from_day: float, to_day: float):
    """
    Sets start time and stop time to param.in file.
    :param from_day:
    :param to_day:
    :return:
    """
    def _edit_file(filepath: str, callback: Callable[[Iterable[str], TextIO], None]):
        with open(filepath) as f:
            out_fname = filepath + ".tmp"
            out = open(out_fname, "w")
            callback(f, out)
            out.close()
            os.rename(out_fname, filepath)

    def _update_params(infile: Iterable[str], outfile: TextIO):
        startday_pattern = ' start time (days)= '
        stopday_pattern = ' stop time (days) = '
        for line in infile:
            if line.startswith(startday_pattern):
                line = '%s%f\n' % (startday_pattern, from_day)
            if line.startswith(stopday_pattern):
                line = '%s%f\n' % (stopday_pattern, to_day)
            outfile.write(line)

    integrator_path = opjoin(Config.get_project_dir(), CONFIG['integrator']['dir'])
    param_in_filepath = opjoin(integrator_path, CONFIG.INTEGRATOR_PARAM_FILENAME)

    _edit_file(param_in_filepath, _update_params)
