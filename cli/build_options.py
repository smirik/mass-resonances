from argparse import Namespace
from argparse import ArgumentParser
from typing import List


def build_options(args: List[str]) -> Namespace:
    startargs = {'metavar': 'START', 'type': int, 'default': 1,
                 'help': 'default 0'}
    stopargs = {'metavar': 'STOP', 'type': int, 'help': 'default START+100'}
    _interval_parser = ArgumentParser(add_help=False)
    _interval_parser.add_argument('--start', **startargs)
    _interval_parser.add_argument('--stop', **stopargs)

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='action')
    parser.add_argument('--loglevel', dest='loglevel', metavar='LEVEL',
                        type=str, default='DEBUG', help='default DEBUG')

    subparsers.add_parser('calc', help='calc --help',
                          parents=[_interval_parser])
    subparsers.add_parser('plot', help='plot --help',
                          parents=[_interval_parser])
    subparsers.add_parser('clean', help='clean --help',
                          parents=[_interval_parser])
    find_parser = subparsers.add_parser('find', help='find --help',
                                        parents=[_interval_parser])
    package_parser = subparsers.add_parser('package', help='package --help',
                                           parents=[_interval_parser])
    extract_parser = subparsers.add_parser('extract', help='extract --help',
                                           parents=[_interval_parser])

    package_parser.add_argument('--res', type=bool, default=False)
    package_parser.add_argument('--aei', type=bool, default=False)
    package_parser.add_argument('--compress', type=bool, default=False)

    find_parser.add_argument('--current', type=bool, default=False)

    extract_parser.add_argument('--copy-aei', type=bool, default=False)

    return parser.parse_args(args)
