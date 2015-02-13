# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from keepluggable import resolve_setting


class Orchestrator(object):
    '''Lives in settings['keepluggable'] as a coordinator of the configured
        classes that compose your personalized solution.
        '''

    def __init__(self, settings):
        self.settings = settings
        self._instantiate_payload_storage()
        self._instantiate_metadata_storage()

        # Get the action classes based on configuration
        self.files_action_cls = resolve_setting(
            self.settings, 'files_action_cls',
            'keepluggable.actions:BaseFilesAction')

    def _instantiate_payload_storage(self):
        '''Instantiate a payload storage strategy based on configuration.'''
        storage_cls = resolve_setting(self.settings, 'storage_file')
        self.storage_file = storage_cls(self.settings)

    def _instantiate_metadata_storage(self):
        '''Instantiate a metadata storage strategy based on configuration.'''
        storage_cls = resolve_setting(self.settings, 'storage_metadata')
        self.storage_metadata = storage_cls(self.settings)
