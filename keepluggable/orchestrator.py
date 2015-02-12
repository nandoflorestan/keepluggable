# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from bag import resolve
from keepluggable import read_setting


class Orchestrator(object):
    '''Lives in settings['keepluggable'] as a coordinator of the configured
        classes that compose your personalized solution.
        '''

    def __init__(self, settings):
        self.settings = settings

        # Instantiate a storage strategy based on configuration
        storage_cls = self.resolve('storage_file')
        self.storage_file = storage_cls(settings)

        # Get the model classes based on configuration
        self.file_model_cls = self.resolve('file_model_cls')

        # Get the action classes based on configuration
        self.files_action_cls = self.resolve(
            'files_action_cls', 'keepluggable.actions:BaseFilesAction')

    def resolve(self, key, default=None):
        resource_spec = read_setting(self.settings, key, default)
        return resolve(resource_spec)
