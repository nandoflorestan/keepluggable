# -*- coding: utf-8 -*-

"""Integration with the Pyramid web framework."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from configparser import ConfigParser
from keepluggable.orchestrator import Orchestrator

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory('keepluggable')
del TranslationStringFactory


def get_orchestrator(ini_path):
    """Return an Orchestrator instance."""
    parser = ConfigParser()
    parser.read(ini_path)
    try:
        section = parser['keepluggable']
    except KeyError:
        raise RuntimeError(
            'There is no [keepluggable] section in the config file.')
    # TODO Instantiate a configured Orchestrator subclass instead:
    return Orchestrator(section)


def includeme(config):
    config.scan('keepluggable.web.pyramid')
    # Read the 'keepluggable' section of the current .ini file
    ini_path = config.registry.settings['__file__']
    # Instantiate the orchestrator and make it globally available
    config.registry.settings['keepluggable'] = get_orchestrator(ini_path)
