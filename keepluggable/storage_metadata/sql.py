# -*- coding: utf-8 -*-

'''File metadata storage backend using SQLAlchemy.

To use this, you must create a subclass and override the ``_get_session()``
method.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from keepluggable import resolve_setting


class SQLAlchemyMetadataStorage(object):
    __doc__ = __doc__

    def __init__(self, settings):
        self.settings = settings

        # TODO Obtain the model classes from the configuration
        self.file_model_cls = resolve_setting(
            self.settings, 'sql.file_model_cls')

    def _get_session(self):
        raise NotImplementedError()

    def create_file_metadata(self, metadata):
        sas = self._get_session()
        model_instance = self.file_model_cls(**metadata)
        sas.add(model_instance)
