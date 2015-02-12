# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class BaseFilesAction(object):
    def __init__(self, orchestrator, bucket):
        self.orchestrator = orchestrator
        self.bucket = bucket

    def store_original_file(self, bytes_io, file_name, mime_type, encoding):
        '''Point of entry into the workflow of storing a file.
            This method will usually be overridden in subclasses.
            '''
        # TODO Instantiate the metadata model
        fil = self.orchestrator.file_cls(
            file_name=file_name, mime_type=mime_type)
        # Hook for subclasses to avoid storing this file
        if not self._can_store(bytes_io, fil, encoding):
            return
        # TODO What to do with the original filename?
        # TODO Calculate the md5
        if fil.mime_type1 == 'image':
            return self.store_image(bytes_io, md5, fil)
        else:
            return self.store_non_image(bytes_io, md5, fil)

    def _can_store(self, bytes_io, fil, encoding):
        'Override this method if you wish to abort storing some files early.'
        return True

    def store_non_image(self, bytes_io, md5, fil):
        self.orchestrator.storage_file.put_object(
            bucket=self.bucket, key=md5, bytes_io=bytes_io)
        # TODO Store the original payload
        return fil

    def store_image(self, bucket, filename, content):
        # TODO Apply self.image_resize_policy
        # TODO Store metadata
        # TODO Store aspect ratio
        # TODO Call store_file
        pass
