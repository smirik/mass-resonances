import logging
import math


def logging_done():
    logging.info('[done]')


def cutoff_angle(value: float) -> float:
    """Cutoff input angle to interval from 0 to 2Pi or from 0 to -2Pi
    if input angle is negative.

    :param float value:
    :rtype: float
    :return: angle in interval [0; 2Pi] or [0; -2Pi]
    """
    if value > math.pi:
        while value > math.pi:
            value -= 2*math.pi
    else:
        while value < -math.pi:
            value += 2*math.pi
    return value


# def cutoff_angle(value: float) -> float:
#     """Cutoff input angle to interval from 0 to 2Pi or from 0 to -2Pi
#     if input angle is negative.
#
#     :param float value:
#     :rtype: float
#     :return: angle in interval [0; 2Pi] or [0; -2Pi]
#     """
#     n = int(value / math.pi)
#     return value - (n * math.pi)

