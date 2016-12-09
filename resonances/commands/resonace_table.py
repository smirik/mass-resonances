from resonances.settings import Config
import math
from typing import Dict
from enum import Enum
from enum import unique
from typing import List
from fractions import gcd


@unique
class _FormatEnum(Enum):
    tex = 'tex'
    simple = 'simple'


CONFIG = Config.get_params()
FORMAT = _FormatEnum(CONFIG['resonance_table']['format'])
_Body = Dict[str, float]
_AXIS_MIN = 1.5


_PLANET_NUMBER = {
    'VENUS': 2,
    'EARTH': 3,
    'MARS': 4,
    'JUPITER': 5,
    'SATURN': 6,
    'URANUS': 7,
    'NEPTUNE': 8,
}


class _ResonanceGeneratorBuilder:
    def __init__(self, body_count: int, order_max: int):
        self.body_count = body_count

        if order_max is not None:
            self.order_max = order_max
        elif body_count == 2:
            self.order_max = 7
        else:
            self.order_max = 25

    def build(self):
        if self.body_count == 2:
            return self._3b_resonance_gen()
        else:
            return self._2b_resonance_gen()

    def _3b_resonance_gen(self):
        for i in range(1, 9):
            for j in range(-self.order_max, self.order_max + 1):
                for k in range(-self.order_max, self.order_max + 1):
                    diff = int(0.0 - i - j - k)
                    if i == 0 or j == 0 or k == 0 or abs(diff) > self.order_max:
                        continue
                    resonance = [i, j, k, 0, 0, diff]
                    yield resonance

    def _2b_resonance_gen(self):
        for i in range(1, self.order_max + 1):
            for j in range(1, self.order_max + 1):
                if i < j or gcd(i, j) > 1:
                    continue
                diff = i - j
                resonance = [i, -j, 0, -diff]
                yield resonance


def _build_line_data(resonance: List[int], axis: float) -> str:
    if (FORMAT == _FormatEnum.tex):
        line_data = ' & '.join(str(x) for x in resonance) + ' & %2.4f \\\\' % axis
    else:
        line_data = ' '.join(str(x) for x in resonance) + ' %2.4f' % axis
    return line_data


def generate_resonance_table(body_names: List[str], axis_max: float = None,
                             order_max: int = None) -> List[str]:
    """
    Generates resonance table.
    """
    data = []

    body_count = len(body_names)
    builder = _ResonanceGeneratorBuilder(body_count, order_max)
    for resonance in builder.build():
        if body_count == 2:
            try:
                bodies = [_build_body(x) for x in body_names]
                axis = _build_resonance_axis(resonance, bodies)
            except _MeanMotionException:
                pass
                continue
            if abs(resonance[5]) >= builder.order_max or axis <= _AXIS_MIN:
                continue
            if axis_max is not None and axis >= axis_max:
                continue
            line_data = _build_line_data(resonance, axis)
        elif body_count == 1:
            body_axis = _build_body(body_names[0])['axis']
            ratio = (-resonance[1]) / resonance[0]
            axis = body_axis * (ratio ** (2/3))
            line_data = _build_line_data(resonance, axis)
        else:
            raise Exception('Unexpected count of bodies.')
        pass
        data.append(line_data)
    return data


class _MeanMotionException(Exception):
    pass


def _build_resonance_axis(resonance, bodies: List[_Body]) -> float:
    jupiter = bodies[0]
    body_count = len(bodies)
    K = CONFIG['constants']['k']

    items = []
    for i, body in enumerate(bodies):
        items.append(-resonance[i] * body['mean_motion'])
        items.append(-resonance[i + body_count + 1] * body['longitude_of_periapsis'])
    lin_combination = sum(items)
    mean_motion = lin_combination / resonance[2]
    if mean_motion < 0:
        raise _MeanMotionException()

    axis = (K / mean_motion) ** (2.0/3)
    eps = (jupiter['axis'] - axis) / jupiter['axis']
    longitude_of_periapsis = (
        K / (2 * math.pi) * math.sqrt(axis / jupiter['axis']) *
        (eps ** 2) * jupiter['mean_motion']
    )
    mean_motion = (lin_combination - resonance[2] * longitude_of_periapsis) / resonance[2]
    if mean_motion < 0:
        raise _MeanMotionException()

    axis = (K / mean_motion) ** (2.0/3)
    return axis


def _build_body(by_name: str) -> _Body:
    planet_index = _PLANET_NUMBER[by_name]
    constants = CONFIG['constants']
    longitude_of_periapsis = _from_day_to_year(_from_sec(
        constants['longitude_of_periapsis'][planet_index]))
    mean_motion = _from_day_to_year(_from_sec(
        constants['mean_motion'][planet_index]))
    res = {
        'axis': constants['axis'][planet_index],
        'mean_motion': mean_motion,
        'longitude_of_periapsis': float("%.6f" % longitude_of_periapsis)
    }
    return res


def _from_sec(value):
    return (value/3600.0)*math.pi/180.0


def _from_day_to_year(value):
    return value / 365.25
