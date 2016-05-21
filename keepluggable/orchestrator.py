# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from zope.interface import Interface, implementer, Attribute


class IOrchestrator(Interface):
    """Represents the materialization of the components chosen in settings."""

    storage_file = Attribute('payload storage strategy')
    storage_metadata = Attribute('metadata storage strategy')
    files_action_cls = Attribute('action strategy')


@implementer(IOrchestrator)
class Orchestrator(object):
    """The coordinator of your configured components."""

    def __init__(self, name, settings):
        """``settings`` contains only the relevant section of the INI file."""
        self.name, self.settings = name, settings
        self._instantiate_payload_storage()
        self._instantiate_metadata_storage()
        self._resolve_files_action_class()

    def _instantiate_payload_storage(self):
        storage_cls = self.settings.resolve('storage.file')
        self.storage_file = storage_cls(self)

    def _instantiate_metadata_storage(self):
        storage_cls = self.settings.resolve('storage.metadata')
        self.storage_metadata = storage_cls(self)

    def _resolve_files_action_class(self):
        self.files_action_cls = self.settings.resolve('action.files')
