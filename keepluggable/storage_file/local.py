# -*- coding: utf-8 -*-

'''Local filesystem storage backend.

    You should use this for testing only because it is not very robust.
    It stores files in a very simple directory scheme::

        base_storage_directory / bucket_name / md5

    To enable this backend, use this configuration::

        storage.file = keepluggable.storage_file.local:LocalFilesystemStorage

    Configuration settings
    ======================

    - ``local.base_directory``: Where to store payloads
    '''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pathlib import Path
from time import time
from keepluggable import read_setting
from . import BasePayloadStorage

MEGABYTE = 1048576


class LocalFilesystemStorage(BasePayloadStorage):
    __doc__ = __doc__

    def __init__(self, settings):
        self.directory = Path(
            read_setting(settings, 'local.base_directory')).absolute()
        if not self.directory.exists():
            self.directory.mkdir(parents=True)

    def create_bucket(self, name):
        (self.directory / name).mkdir()

    def delete_bucket(self, bucket):
        for key in self.gen_objects(bucket):
            self.delete_object(bucket, key)
        (self.directory / bucket).rmdir()

    @property
    def _buckets(self):
        return (d for d in self.directory.iterdir() if d.is_dir())

    @property
    def bucket_names(self):  # generator
        return (b.name for b in self._buckets)

    def gen_objects(self, bucket):
        '''Generator of the keys in a bucket.'''
        return (d.name for d in (self.directory / bucket).iterdir())

    def get_content(self, bucket, key):
        return open(self.directory / bucket / key, 'rb')

    def put_object(self, bucket, metadata, bytes_io):
        outfile = self.directory / bucket / metadata['md5']
        with open(str(outfile), mode='wb', buffering=MEGABYTE) as writer:
            while True:
                chunk = bytes_io.read(MEGABYTE)
                if chunk:
                    writer.write(chunk)
                else:
                    break
        assert outfile.lstat().st_size == metadata['length']

    def delete_object(self, bucket, key):
        (self.directory / bucket / key).unlink()

    def get_url(self, bucket, key, seconds=3600, https=False):
        '''Returns only a "file://" URL for local testing. For more adequate
            URLs you should override this method and use your web framework.
            '''
        # seconds = int(time()) + seconds
        return 'file://{directory}/{bucket}/{key}'.format(
                directory=self.directory, bucket=bucket, key=key)
