import logging
import sys
from argparse import Namespace

from commands import calc, plot, package, remove_export_directory, find
from settings import ConfigSingleton
from storage import extract

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

    def find(self):
        find(self._commandline_options.start, self.stop)

    def extract(self):
        extract(self._commandline_options.start,
                do_copy_aei=self._commandline_options.copy_aei)

