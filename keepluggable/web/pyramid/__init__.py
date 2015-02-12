# -*- coding: utf-8 -*-

'''Integration with the Pyramid web framework.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from configparser import ConfigParser
from keepluggable.orchestrator import Orchestrator


def includeme(config):
    config.scan('keepluggable.web.pyramid')

    # Read the 'keepluggable' section of the current .ini file
    parser = ConfigParser()
    path = config.registry.settings['__file__']
    parser.read(path)
    try:
        section = parser['keepluggable']
    except KeyError:
        raise RuntimeError(
            'There is no [keepluggable] section in the config file.')

    # Instantiate the orchestrator and make it globally available
    config.registry.settings['keepluggable'] = Orchestrator(section)
    # TODO Instantiate a configured Orchestrator subclass instead.
