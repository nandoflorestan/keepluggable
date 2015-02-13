# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class BaseFilesAction(object):
    def __init__(self, orchestrator, bucket):
        self.orchestrator = orchestrator
        self.bucket = bucket

    def store_original_file(self, bytes_io, **metadata):
        '''Point of entry into the workflow of storing a file.
            This method will usually be overridden in subclasses.
            '''
        assert metadata['file_name']

        # This is not a derived file such as a resized image.
        metadata['version'] = 'original'

        self._guess_mime_type(metadata)

        # Hook for subclasses to avoid storing this file
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
        'Override this method if you wish to abort storing some files early.'
        return True

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
        metadata['length'] = the_length
        bytes_io.seek(0)  # ...so it can be read again

    def _store_file(self, bytes_io, metadata):
        '''Saves the payload and the metadata on the 2 storage backends.'''
        self.orchestrator.storage_metadata.create_file_metadata(metadata)
        self.orchestrator.storage_file.put_object(
            bucket=self.bucket, metadata=metadata, bytes_io=bytes_io)

    def _before_storing_image(self, bytes_io, metadata):
        # TODO Apply self.image_resize_policy
        # TODO Store metadata['image_width']
        # TODO Store metadata['image_height']
        pass

    def _after_storing_image(self, bytes_io, metadata):
        pass
