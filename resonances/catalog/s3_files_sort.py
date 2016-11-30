#!/usr/bin/env python
import sys
from datetime import datetime


def _get_interval(from_line: str):
    starts_from = from_line.index('aei-') + 4
    ends_by = from_line.index('-', starts_from)
    start_asteroid_number = int(from_line[starts_from: ends_by])

    starts_from = ends_by + 1
    ends_by = from_line.index('.tar', starts_from)
    stop_asteroid_number = int(from_line[starts_from:ends_by])
    return start_asteroid_number, stop_asteroid_number


def _sort_function(line):
    start_asteroid_number, stop_asteroid_number = _get_interval(line)
    return start_asteroid_number


def main():
    path = sys.argv[1]
    file_data = []
    with open(path) as s3file:
        for line in s3file:
            file_data.append(line)

    with open('%s.%s.backup' % (path, datetime.now().timestamp()), 'w') as s3file:
        s3file.writelines(file_data)

    sorted_list = sorted(file_data, key=_sort_function)

    with open(path, 'w') as s3file:
        s3file.writelines(sorted_list)


if __name__ == '__main__':
    main()
