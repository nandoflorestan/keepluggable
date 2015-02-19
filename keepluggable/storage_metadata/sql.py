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

        self.file_model_cls = resolve_setting(
            self.settings, 'sql.file_model_cls')

        # Instantiate a session at startup just to make sure it is configured
        self._get_session()

    def _get_session(self):
        '''Returns the SQLAlchemy session.'''
        return resolve_setting(self.settings, 'sql.session')

    def create_bucket(self, bucket_id, bucket_name):
        pass  # In SQL we don't need to do anything to create a bucket.

    def put_metadata(self, metadata, bucket_id, bucket_name):
        '''Create or update a file corresponding to the given ``metadata``.
            This method returns a 2-tuple containing the ID of the entity
            and a boolean saying whether the entity is new or existing.

            It is not likely that this method should be overridden.
            '''
        sas = self._get_session()
        entity = self._find(sas, metadata, bucket_id, bucket_name)
        is_new = entity is None
        if is_new:
            entity = self._instantiate(
                sas, metadata, bucket_id, bucket_name)
            sas.add(entity)
        else:
            self._update(sas, metadata, bucket_id, bucket_name, entity)
        sas.flush()
        return entity.id, is_new

    def _find(self, sas, metadata, bucket_id, bucket_name):
        '''Override this to search for an existing file.'''
        return sas.query(self.file_model_cls).filter_by(
            md5=metadata['md5']).first()

    def _update(self, sas, metadata, bucket_id, bucket_name, entity):
        '''Override this to update the metadata of an existing entity.'''
        for key, value in metadata.items():
            setattr(entity, key, value)

    def _instantiate(self, sas, metadata, bucket_id, bucket_name):
        '''Override this to add or delete arguments on the constructor call.'''
        return self.file_model_cls(**metadata)

    def gen_objects(self, bucket):
        '''Generator of the keys in a bucket.'''
        raise NotImplementedError()

    def get_metadata(self, bucket_id, bucket_name, key):
        '''Returns a dict containing the metadata of one file.'''
        raise NotImplementedError()

    def delete_metadata(self, bucket_id, bucket_name, key):
        raise NotImplementedError()  # but a sketch follows:
        sas = self._get_session()
        sas.query(self.file_model_cls).filter_by(  # Missing criteria here
            ).delete()
