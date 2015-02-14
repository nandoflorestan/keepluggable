# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from keepluggable import read_setting
from keepluggable.exceptions import FileNotAllowed


class BaseFilesAction(object):
    '''Configuration settings used by this component:

        - ``max_file_size`` (int): the maximum file length, in bytes, that
          can be stored. When absent, the system does not have a maximum size.
        '''

    def __init__(self, orchestrator, bucket):
        self.orchestrator = orchestrator
        self.bucket = bucket

    def store_original_file(self, bytes_io, **metadata):
        '''Point of entry into the workflow of storing a file.
            You can override this method in subclasses to change the steps
            since it is a sort of coordinator that calls one method for
            each step.

            The argument *bytes_io* is a file-like object with the payload.
            *metadata* is a dict with the information to be persisted in
            the metadata storage.
            '''
        assert metadata['file_name']

        # This is not a derived file such as a resized image.
        metadata['version'] = 'original'

        self._guess_mime_type(metadata)

        self._compute_length(bytes_io, metadata)

        # Hook for subclasses to allow or forbid storing this file
        self._allow_storage_of(bytes_io, metadata)  # may raise FileNotAllowed

        self._compute_md5(bytes_io, metadata)

        is_image = metadata['mime_type'].startswith('image')
        if is_image:
            self._before_storing_image(bytes_io, metadata)
        self._store_file(bytes_io, metadata)
        if is_image:
            self._after_storing_image(bytes_io, metadata)
        return metadata

    def _guess_mime_type(self, metadata):
        '''Fill in the mime_type if not already known.'''
        t = metadata.get('mime_type')
        if t is None:
            from mimetypes import guess_type
            metadata['mime_type'] = guess_type(metadata['file_name'])[0]

    def _allow_storage_of(self, bytes_io, metadata):
        '''Override this method if you wish to abort storing some files.
            To abort, raise FileNotAllowed with a message explaining why.'''
        maximum = int(read_setting(
            self.orchestrator.settings, 'max_file_size', default=None))
        if maximum is not None and metadata['length'] > maximum:
            raise FileNotAllowed(
                'The file is {} KB long and the maximum is {} KB.'.format(
                    int(metadata['length'] / 1024), int(maximum / 1024)))

    def _compute_length(self, bytes_io, metadata):
        from bag.streams import get_file_size
        metadata['length'] = get_file_size(bytes_io)

    def _compute_md5(self, bytes_io, metadata):
        from hashlib import md5
        two_megabytes = 1048576 * 2
        the_hash = md5()
        the_length = 0
        while True:
            segment = bytes_io.read(two_megabytes)
            if segment == b'':
                break
            the_length += len(segment)
            the_hash.update(segment)
        metadata['md5'] = the_hash.hexdigest()
        previous_length = metadata.get('length')
        if previous_length is None:
            metadata['length'] = the_length
        else:
            assert previous_length == the_length, "Bug? File lengths {}, {} " \
                "don't match.".format(previous_length, the_length)
        bytes_io.seek(0)  # ...so it can be read again

    def _before_storing_image(self, bytes_io, metadata):
        # TODO Apply self.image_resize_policy
        # TODO Store metadata['image_width']
        # TODO Store metadata['image_height']
        pass

    def _store_file(self, bytes_io, metadata):
        '''Saves the payload and the metadata on the 2 storage backends.'''
        # TODO Enable file storage soon:
        # self.orchestrator.storage_file.put_object(
        #     bucket=self.bucket, metadata=metadata, bytes_io=bytes_io)

        metadata['id'] = \
            self.orchestrator.storage_metadata.create_file_metadata(metadata)

    def _after_storing_image(self, bytes_io, metadata):
        # TODO Store different sizes
        pass
