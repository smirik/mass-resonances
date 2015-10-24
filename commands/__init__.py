from ..settings import ConfigSingleton
import logging
import subprocess
from ..catalog import AstDys


class Command(object):
    CONFIG = ConfigSingleton.get_singleton()

    @classmethod
    def calc(cls, start: int):
        num_b = cls.CONFIG['integrator']['number_of_bodies']
        logging.info(
            'Create initial conditions for asteroids from #%i to #%i' %
            (start, start + num_b)
        )

        for i in num_b['times']:
            num = i + start
            AstDys.find_by_num(num)

        logging.info('Integrating orbits...')
