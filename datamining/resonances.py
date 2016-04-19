import logging
from typing import Iterable, Tuple, List
from entities import ThreeBodyResonance
from entities.body import Asteroid
from entities.dbutills import session
from os.path import join as opjoin
from settings import Config
from sqlalchemy.orm import joinedload

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
MERCURY_DIR = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'])


def get_resonances(start: int, stop: int, only_librations: bool) -> Iterable[ThreeBodyResonance]:
    """
    Returns resonances related to asteroid in pointer interval from start to stop.
    :param start: start of interval of asteroid numbers.
    :param stop: finish of interval of asteroid numbers.
    :param only_librations: flag indicates about getting resonances, that has related librations.
    :return:
    """
    names = ['A%i' % x for x in range(start, stop)]
    resonances = session.query(ThreeBodyResonance)\
        .options(joinedload('small_body')).join(ThreeBodyResonance.small_body) \
        .options(joinedload('first_body')).options(joinedload('second_body')) \
        .filter(Asteroid.name.in_(names)).options(joinedload('librations'))
    if only_librations:
        resonances = resonances.options(joinedload('libration')).join('libration')
    resonances = sorted(resonances.all(), key=lambda x: x.asteroid_number)

    if not resonances:
        logging.info('We have no resonances, try command load-resonances --start=%i --stop=%i'
                     % (start, stop))

    for resonance in resonances:
        yield resonance


def get_aggregated_resonances(from_asteroid: int, to_asteroid: int, only_librations: bool)\
        -> Iterable[Tuple[ThreeBodyResonance, List[str]]]:
    """Find resonances from /axis/resonances by asteroid axis. Currently
    described by 7 items list of floats. 6 is integers satisfying
    D'Alembert rule. First 3 for longitutes, and second 3 for longitutes
    perihilion. Seventh value is asteroid axis.

    :param only_librations: flag indicates about getting resonances, that has related librations.
    :param to_asteroid:
    :param from_asteroid:
    :return:
    """

    class _DataGetter:
        def __init__(self):
            self._asteroid_number = None
            self._aei_data = []

        def get_aei_data(self, for_asteroid_number: int) -> List[str]:
            if for_asteroid_number != self._asteroid_number:
                self._asteroid_number = for_asteroid_number
                self._aei_data.clear()

                smallbody_filepath = opjoin(MERCURY_DIR, 'A%i.aei' % self._asteroid_number)
                with open(smallbody_filepath) as aei_file:
                    for line in aei_file:
                        self._aei_data.append(line)

            return self._aei_data

    aei_getter = _DataGetter()
    for resonance in get_resonances(from_asteroid, to_asteroid, only_librations):
        aei_data = aei_getter.get_aei_data(resonance.asteroid_number)
        assert len(aei_data) > 0
        yield resonance, aei_data
