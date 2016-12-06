from os.path import join as opjoin
from os import remove
from os.path import join as opexists
from typing import Tuple
from resonances.settings import Config
from resonances.commands import load_resonances as _load_resonances
from resonances.datamining import PhaseStorage
from resonances.commands import calc as _calc
from resonances.commands import LibrationFinder
from resonances.catalog import PossibleResonanceBuilder
from abc import abstractmethod
from enum import Enum
from enum import unique

CONFIG = Config.get_params()
RESONANCE_TABLE_FILE = CONFIG['resonance_table']['file']
PROJECT_DIR = Config.get_project_dir()
RESONANCE_FILEPATH = opjoin(PROJECT_DIR, 'axis', RESONANCE_TABLE_FILE)
STEP = CONFIG['integrator']['number_of_bodies']


@unique
class IntegrationState(Enum):
    start = 0
    calc = 1
    load = 2
    find = 3


Interval = Tuple[int, int]


class Integration:
    def __init__(self):
        if opexists(self.state_file):
            self.open()
        else:
            self._state = IntegrationState.start

    def save(self, state: IntegrationState):
        with open(self.state_file, 'w') as fd:
            fd.write(self.state)
        self._state = state

    def open(self):
        with open(self.state_file, 'r') as fd:
            self._state = IntegrationState(int(fd.read(1)))

    @property
    def state_file(self) -> str:
        return opjoin('/tmp', 'Integration_state.txt')

    @property
    def state(self) -> IntegrationState:
        return self._state


class ACommand(object):
    def __init__(self, integration: Integration, interval: Interval):
        self._integration = integration
        self._start = interval[0]
        self._stop = interval[1]

    @abstractmethod
    def exec(self):
        pass


class CalcCommand(ACommand):
    def __init__(self, integration: Integration, interval: Interval,
                 from_day: float, to_day: float):
        super(CalcCommand, self).__init__(integration)
        self._from_day = from_day
        self._to_day = to_day
        self._state = IntegrationState.calc

    def exec(self):
        if self._integration.state == IntegrationState.start:
            _calc(self._interval[0], self._interval[1], STEP,
                  self._from_day, self._to_day, self.aei_path)
            self._integration.save(self._state)

    @property
    def aei_path(self):
        return opjoin('/tmp', 'aei')


class LoadCommand(ACommand):
    def __init__(self, integration: Integration, interval: Interval,
                 planets: Tuple[str], catalog: str, axis_swing: float, gen: bool):
        super(LoadCommand, self).__init__(integration)
        self._builder = PossibleResonanceBuilder(planets, axis_swing, catalog)
        self._gen = gen
        self._state = IntegrationState.load

    def exec(self):
        if self._integration.state == IntegrationState.calc:
            self._integration.state = IntegrationState.load
            for i in range(self._start, self._stop, STEP):
                end = i + STEP if i + STEP < self._stop else self._stop
                _load_resonances(RESONANCE_FILEPATH, i, end, self._builder, self._gen)
            self._integration.save(self._state)


class FindCommand(ACommand):
    def __init__(self, integration: Integration, interval: Interval,
                 planets: Tuple[str], aei_path: str):
        super(FindCommand, self).__init__(integration, interval)
        self._aei_path = aei_path
        self._finder = LibrationFinder(planets, False, True, False, False, PhaseStorage.file, True)
        self._state = IntegrationState.find

    def exec(self):
        if self._integration.state == IntegrationState.load:
            self._integration.state = IntegrationState.find
            self._finder.find_by_file(self._aei_path)
            for i in range(self._start, self._stop, STEP):
                end = i + STEP if i + STEP < self._stop else self._stop
                self._finder.find(i, end, self._aei_path)
            self._integration.save(self._state)


def integrate(start: int, stop: int, from_day: float, to_day: float, planets: Tuple[str],
              catalog: str, axis_swing: float, gen: bool = False):
    integration = Integration()
    intervnal = (start, stop)
    calcCmd = CalcCommand(integration, intervnal, from_day, to_day)
    commands = [
        calcCmd,
        LoadCommand(integration, intervnal, planets, catalog, axis_swing, gen),
        FindCommand(integration, intervnal, planets, calcCmd.aei_path),
    ]

    for cmd in commands:
        cmd.exec()

    remove(integration.state_file)
