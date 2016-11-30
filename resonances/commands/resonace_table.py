from resonances.settings import Config
import math
from typing import Dict
from enum import Enum
from enum import unique


@unique
class FormatEnum(Enum):
    tex = 'tex'
    simple = 'simple'


CONFIG = Config.get_params()
FORMAT = FormatEnum(CONFIG['resonance_table']['format'])
Body = Dict[str, float]
MAX_ORDER = 7


_PLANET_NUMBER = {
    'VENUS': 2,
    'EARTH': 3,
    'MARS': 4,
    'JUPITER': 5,
    'SATURN': 6,
    'URANUS': 7,
    'NEPTUNE': 8,
}


def generate_resonance_table(body1: str, body2: str):
    """
    Generates resonance table
    """
    for i in range(1, 9):
        for j in range(-MAX_ORDER, MAX_ORDER+1):
            for k in range(-MAX_ORDER, MAX_ORDER+1):
                diff = int(0.0 - i - j - k)
                if i == 0 or j == 0 or k == 0 or abs(diff) > MAX_ORDER:
                    continue
                resonance = [i, j, k, 0, 0, diff]
                try:
                    asteroid = _build_asteroid(resonance, _build_body(body1), _build_body(body2))
                except MeanMotionException:
                    continue
                if abs(diff) < MAX_ORDER and asteroid['axis'] > 1.5:
                    if (asteroid.axis != 0):
                        line_data = (resonance[0], resonance[1], resonance[2],
                                     resonance[5], asteroid['axis'])
                        if (FORMAT == FormatEnum.tex):
                            print("%d & %d & %d & %d & %2.4f \\\\ \n" % line_data)
                        elif (format == 'simple'):
                            print("%d %d %d 0 0 %d %2.4f \n" % line_data)
                        else:
                            print("%d %d %d 0 0 %d %2.4f \n" % line_data)


class MeanMotionException(Exception):
    pass


def _build_asteroid(resonance, jupiter: Body, saturn: Body) -> Body:
    K = CONFIG['constants']['k']
    lin_combination = sum([
        -resonance[0] * jupiter['mean_motion'],
        -resonance[1] * saturn['mean_motion'],
        -resonance[3] * jupiter['longitude_of_periapsis'],
        -resonance[4] * saturn['longitude_of_periapsis'],
    ])
    mean_motion = lin_combination / resonance[2]
    if mean_motion < 0:
        raise MeanMotionException()

    axis = (K / (mean_motion))**(2.0/3)
    eps = (jupiter['axis'] - axis) / jupiter['axis']
    longitude_of_periapsis = (K / (2 * math.pi) *
                              math.sqrt(axis / jupiter['axis']) *
                              (eps ** 2) *
                              jupiter['mean_motion'])
    mean_motion = (lin_combination - resonance[2] * longitude_of_periapsis) / resonance[2]

    asteroid = {
        'axis': (K / (mean_motion))**(2.0/3),
        'mean_motion': mean_motion,
        'longitude_of_periapsis': longitude_of_periapsis
    }
    return asteroid


def _build_body(by_name: str) -> Body:
    planet_index = _PLANET_NUMBER[by_name]
    constants = CONFIG['constants']
    longitude_of_periapsis = from_day_to_year(from_sec(
        constants['longitude_of_periapsis'][planet_index]))
    res = {
        'axis': constants['axis'][planet_index],
        'mean_motion': constants['mean_motion'][planet_index],
        'longitude_of_periapsis': longitude_of_periapsis
    }
    return res


def from_sec(value):
    return (value/3600.0)*math.pi/180.0


def from_day_to_year(value):
    return value / 365.25
