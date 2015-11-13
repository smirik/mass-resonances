#!/usr/bin/env python
import logging
import sys

from cli import ActionBridge
from cli import build_options
from settings import ConfigSingleton

__verion__ = '0.0.1'
CONFIG = ConfigSingleton.get_singleton()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']
GETS = 0


def main():
    options = build_options(sys.argv[1:])

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
        options.stop = options.start + BODIES_COUNTER

    bridge = ActionBridge(options)
    command = getattr(bridge, options.action)
    command()


if __name__ == '__main__':
    main()
