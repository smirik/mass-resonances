import logging
import math


def logging_done():
    logging.info('[done]')


def cutoff_angle(value: float) -> float:
    """Cutoff input angle to interval from 0 to Pi or from 0 to -Pi
    if input angle is negative.

    :param float value:
    :rtype: float
    :return: angle in interval [0; Pi] or (0; -Pi]
    """
    if value > math.pi:
        while value > math.pi:
            value -= 2*math.pi
    else:
        while value < -math.pi:
            value += 2*math.pi
    return value
