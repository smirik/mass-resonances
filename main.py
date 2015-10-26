#!/usr/bin/env python
import logging
from optparse import OptionParser
from commands import Command

from settings import ConfigSingleton

parser = OptionParser()
parser.add_option('--start', dest='start', metavar='N', type='int')
parser.add_option('--stop', dest='stop', metavar='N', type='int')
parser.add_option('--action', dest='action', metavar='ACTION', type='str')
parser.add_option('--loglevel', dest='loglevel', metavar='LEVEL', type='str')


def main():
    CONFIG = ConfigSingleton.get_singleton()
    GETS = 0
    (options, args) = parser.parse_args()

    level = 'DEBUG'
    if options.loglevel:
        level = options.loglevel.upper()

    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, level)
    )

    if not options.action:
        logging.error('Specify action')
        return

    action = options.action

    if options.start:
        start = options.start
    else:
        logging.warning('Please, specify first object number')
        start = GETS

    if options.stop:
        stop = options.stop
    else:
        stop = start + CONFIG['integrator']['number_of_bodies']

    Command.calc(start)


if __name__ == '__main__':
    main()
