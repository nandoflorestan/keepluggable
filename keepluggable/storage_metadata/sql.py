# -*- coding: utf-8 -*-

'''File metadata storage backend base class using SQLAlchemy.

    This class certainly needs to be subclassed for your specific use case.
    You must examine the source code and override methods as necessary.
    The most important reason for this is that each application will need
    to namespace the stored files differently.

    Configuration settings
    ======================

    - ``sql.file_model_cls`` must point to a certain model class to store
      the file metadata.
    - ``sql.session`` should point to a scoped session global variable.
      But instead of using this setting, you may override the
      ``_get_session()`` method.

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

    def put(self, namespace, metadata, sas=None):
        '''Create or update a file corresponding to the given ``metadata``.
            This method returns a 2-tuple containing the ID of the entity
            and a boolean saying whether the entity is new or existing.

            Instead of overriding this method, it is probably better for
            you to override the methods it calls.
            '''
        sas = sas or self._get_session()
        entity = self._query(namespace, key=metadata['md5'], sas=sas).first()
        is_new = entity is None
        if is_new:
            entity = self._instantiate(namespace, metadata, sas=sas)
            sas.add(entity)
        else:
            self._update(namespace, metadata, entity, sas=sas)
        sas.flush()
        return entity.id, is_new

    def _query(self, namespace, key=None, sas=None):
        '''Override this to search for an existing file.
            You probably need to do something with the ``namespace``.
            '''
        sas = sas or self._get_session()
        q = sas.query(self.file_model_cls)
        if key is not None:
            q = q.filter_by(md5=key)
        return q

    def _instantiate(self, namespace, metadata, sas=None):
        '''Override this to add or delete arguments on the constructor call.
            You probably need to do something with the ``namespace``.
            '''
        return self.file_model_cls(**metadata)

    def _update(self, namespace, metadata, entity, sas=None):
        '''Override this to update the metadata of an existing entity.
            You might need to do something with the ``namespace``.
            '''
        for key, value in metadata.items():
            setattr(entity, key, value)

    def gen_keys(self, namespace, sas=None):
        '''Generator of the keys in a namespace.'''
        return self._query(sas=sas, namespace=namespace)

    def get(self, namespace, key, sas=None):
        '''Returns a dict containing the metadata of one file,
            or None if not found.
            '''
        entity = self._query(sas=sas, namespace=namespace, key=key).first()
        return entity.to_dict() if entity else None

    def delete(self, namespace, key, sas=None):
        self._query(sas=sas, namespace=namespace, key=key).delete()
