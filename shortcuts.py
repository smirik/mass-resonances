import logging
import math
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket


def logging_done():
    logging.info('[done]')


def is_s3(path) -> bool:
    return 's3://' == path[:5]


def is_tar(path) -> bool:
    return path[-4:] == '.tar' or path[-7:] == '.tar.gz'


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


def create_aws_s3_key(access_key: str, secret_key: str, in_bucket: str, for_path: str) -> Key:
    conn = S3Connection(access_key, secret_key)
    bucket = conn.get_bucket(in_bucket)  # type: Bucket
    start = for_path.index(in_bucket)
    s3_filekey = for_path[start + len(in_bucket) + 1:]
    s3_bucket_key = bucket.new_key(s3_filekey)  # type: Key
    return s3_bucket_key
