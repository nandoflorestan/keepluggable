# -*- coding: utf-8 -*-

'''Integration with the Pyramid web framework. More details in the file
    docs/integration_pyramid.rst
    '''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from keepluggable import SettingsFromFiles, Settings
from keepluggable.orchestrator import IOrchestrator, Orchestrator

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory('keepluggable')
del TranslationStringFactory


def get_orchestrators(ini_path):
    """Reads the INI file looking for sections whose name starts with
        "keepluggable_" and returns a dictionary containing an Orchestrator
        instance for each one.
        """
    PREFIX = 'keepluggable_'
    config = SettingsFromFiles(ini_path)
    orchestrators = []
    for section_name, section_dict in config.adict.items():
        if not section_name.startswith(PREFIX):
            continue
        name = section_name[len(PREFIX):]
        orchestrators.append(Orchestrator(name, Settings(section_dict)))
    if not orchestrators:
        raise RuntimeError('In the config file there is no section starting '
                           'with "keepluggable_".')
    return orchestrators


def includeme(config):
    # config.scan('keepluggable.web.pyramid')  # TODO Unnecessary?
    ini_path = config.registry.settings['__file__']

    # Instantiate the orchestrators and make them available to the Pyramid app:
    for orchestrator in get_orchestrators(ini_path):
        config.registry.registerUtility(
            component=orchestrator,
            provided=IOrchestrator,
            name=orchestrator.name)
