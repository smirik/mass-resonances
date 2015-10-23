#!/usr/bin/python
from optparse import OptionParser
import logging

CONFIG = {}
ACTIONS = ['start', 'stop']
GETS = 0

parser = OptionParser()
parser.add_option('--start', dest='start', metavar='N', type='int')
parser.add_option('--stop', dest='stop', metavar='N', type='int')
parser.add_option('--action', dest='action', metavar='ACTION', type='str')
parser.add_option('--loglevel', dest='loglevel', metavar='LEVEL', type='str')


def main():
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
        logging.error('Specify command')
        return

    action = options.action

    if options.start:
        start = options.start
    else:
        logging.warn('Please, specify first object number')
        start = GETS

    if options.stop:
        stop = options.stop
    else:
        stop = start + CONFIG['integrator']['number_of_bodies']


if __name__ == '__main__':
    main()
