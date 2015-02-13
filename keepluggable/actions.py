# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class BaseFilesAction(object):
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
        if not self._can_store(bytes_io, metadata):
            return

        self._compute_md5(bytes_io, metadata)

        if metadata['mime_type'].startswith('image'):
            self._before_storing_image(bytes_io, metadata)
        self._store_file(bytes_io, metadata)
        if metadata['mime_type'].startswith('image'):
            self._after_storing_image(bytes_io, metadata)
        return metadata

    def _guess_mime_type(self, metadata):
        '''Fill in the mime_type if not already known.'''
        t = metadata.get('mime_type')
        if t is None:
            from mimetypes import guess_type
            metadata['mime_type'] = guess_type(metadata['file_name'])[0]

    def _can_store(self, bytes_io, metadata):
        '''Override this method if you wish to abort storing some files early.
            To abort, raise FileNotAllowed with a message explaining why.'''
        return True

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
        self.orchestrator.storage_metadata.create_file_metadata(metadata)
        # TODO Enable file storage soon:
        # self.orchestrator.storage_file.put_object(
        #     bucket=self.bucket, metadata=metadata, bytes_io=bytes_io)

    def _after_storing_image(self, bytes_io, metadata):
        # TODO Store different sizes
        pass
