from typing import List, Dict
from unittest import mock

import pytest

from resonances.datamining.librations.finder import CirculationYearsFinder, NoPhaseException

PHASES = [
    {'year': 0.0, 'value': -0.51},
    {'year': 3.0, 'value': 0.87},
    {'year': 6.0, 'value': 2.37},
    {'year': 9.0, 'value': -2.51}
]

MORE_PHASES = [
    {'year': 12.0, 'value': 1.51},
    {'year': 15.0, 'value': -1.},
    {'year': 18.0, 'value': 3.1},
]

RESONANCE_ID = 1

VALUES = [
    ([], None, False),
    ([{'year': 0.0, 'value': 1.32}], [], False),
    (PHASES, [PHASES[2]['year']], False),
    (PHASES + [{'year': 12.0, 'value': 0.01}], [PHASES[2]['year']], False),
    (PHASES + [MORE_PHASES[0]], [PHASES[3]['year']], False),
    (PHASES + MORE_PHASES, [PHASES[3]['year'], 15.], False),

    ([], None, True),
    ([{'year': 0.0, 'value': 1.32}], [], True),
    (PHASES, [PHASES[0]['year']], True),
    (PHASES + [MORE_PHASES[0]], [PHASES[0]['year']], True),
    (PHASES + MORE_PHASES, [MORE_PHASES[0]['year']], True),
    (PHASES + [{'year': 12.0, 'value': 0.01}], [PHASES[0]['year'], PHASES[3]['year']], True),
]


@pytest.mark.parametrize('phase_arguments, result_years, for_apocentric', VALUES,
                         ids=VALUES)
@mock.patch('resonances.entities.Phase')
def test_getting_years(Phase, phase_arguments: List[Dict],
                       result_years: List[float], for_apocentric: bool):

    finder = CirculationYearsFinder(RESONANCE_ID, for_apocentric, phase_arguments)
    if result_years is None:
        with pytest.raises(NoPhaseException):
            finder.get_time_breaks()
    else:
        assert finder.get_time_breaks() == result_years
