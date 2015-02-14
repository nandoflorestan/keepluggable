# -*- coding: utf-8 -*-

'''File metadata storage backend using SQLAlchemy. To use this:

    - Either point to your SQLAlchemy session in the configuration setting
      ``sql.session`` or subclass this and override the ``_get_session()``
      method.

    Configuration settings
    ======================

    - ``sql.file_model_cls`` must point to a certain model class to store the file metadata.
    - ``sql.session`` should point to a scoped session global variable.

    TODO: Offer an example of the model class.
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

        # Instantiate a session at startup just to make sure it is configured
        self._get_session()

    def _get_session(self):
        '''Returns the SQLAlchemy session.'''
        return resolve_setting(self.settings, 'sql.session')

    def create_file_metadata(self, metadata):
        sas = self._get_session()
        model_instance = self.file_model_cls(**metadata)
        sas.add(model_instance)
        sas.flush()
        return model_instance.id
