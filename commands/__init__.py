from argparse import Namespace
import logging
import sys

from settings import ConfigSingleton

from .calc import calc
from .plot import plot
from .package import remove_export_directory
from .package import package

CONFIG = ConfigSingleton.get_singleton()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']


class ActionBridge:
    def __init__(self, options: Namespace):
        self._commandline_options = options

    @property
    def stop(self):
        if self._commandline_options.stop <= self._commandline_options.start:
            logging.error('number of STOP asteroid must be greater than number'
                          ' of START asteroid.')
            sys.exit(1)
        if self._commandline_options.stop:
            return self._commandline_options.stop
        return self._commandline_options.start + BODIES_COUNTER

    def calc(self):
        calc(self._commandline_options.start)

    def plot(self):
        plot(self._commandline_options.start, self.stop)

    def package(self):
        package(self._commandline_options.start, self.stop,
                self._commandline_options.res, self._commandline_options.aei,
                self._commandline_options.compress)

    def clean(self):
        remove_export_directory(self._commandline_options.start, self.stop)
