import logging
import math


def logging_done():
    logging.info('[done]')


def is_s3(path) -> bool:
    return 's3://' == path[:5]


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


def get_asteroid_interval(from_line: str):
    starts_from = from_line.index('aei-') + 4
    ends_by = from_line.index('-', starts_from)
    start_asteroid_number = int(from_line[starts_from: ends_by])

    starts_from = ends_by + 1
    ends_by = from_line.index('.tar', starts_from)
    stop_asteroid_number = int(from_line[starts_from:ends_by])
    return start_asteroid_number, stop_asteroid_number

