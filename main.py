#!/usr/bin/env python
import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from typing import List
from settings import ConfigSingleton
from commands import ActionBridge


__verion__ = '0.0.1'
CONFIG = ConfigSingleton.get_singleton()
GETS = 0


def _build_options(args: List[str]) -> Namespace:
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
    package_parser = subparsers.add_parser('package', help='package --help',
                                           parents=[_interval_parser])

    package_parser.add_argument('--res', type=bool, default=False)
    package_parser.add_argument('--aei', type=bool, default=False)
    package_parser.add_argument('--compress', type=bool, default=False)

    return parser.parse_args(args)


def main():
    options = _build_options(sys.argv[1:])

    level = options.loglevel.upper()
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, level)
    )

    if not options.action:
        print('use --help')
        return

    if not options.stop:
        options.stop = options.start+100

    bridge = ActionBridge(options)
    command = getattr(bridge, options.action)
    command()


if __name__ == '__main__':
    main()
