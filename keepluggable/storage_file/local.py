# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from bag.settings import resolve_path
from keepluggable import read_setting
from . import BasePayloadStorage

MEGABYTE = 1048576


class LocalFilesystemStorage(BasePayloadStorage):
    """Local filesystem storage backend.

    You should use this for testing only because it is not very robust.
    It stores files in a very simple directory scheme::

        base_storage_directory / namespace / key

    Performance will suffer as soon as a couple of thousand files are
    stored in a namespace.

    Keys are MD5 hashes by default. To change this, you would modify
    the action, not the storage backend.

    To enable this backend, use this configuration::

        storage.file = keepluggable.storage_file.local:LocalFilesystemStorage

    **Configuration settings**

    Specify in which directory to store payloads like this::

        local.storage_path = some.python.resource:relative/directory
    """

    def __init__(self, settings):
        self.storage_path = read_setting(settings, 'local.storage_path')
        self.directory = resolve_path(self.storage_path).absolute()
        if not self.directory.exists():
            self.directory.mkdir(parents=True)

    def empty_bucket(self, bucket=None):
        """Empty the whole bucket."""
        for namespace in self.namespaces:
            self.delete_namespace(namespace)

    def create_bucket(self, name):
        pass  # This backend ignores buckets.

    @property
    def _namespaces(self):  # generator of Path objects
        return (d for d in self.directory.iterdir() if d.is_dir())

    @property
    def namespaces(self):  # generator of namespace names
        return (n.name for n in self._namespaces)

    def delete(self, namespace, keys, bucket=None):
        """Delete many files."""
        for key in keys:
            path = (self.directory / str(namespace) / key)
            if path.exists():
                path.unlink()

    def gen_keys(self, namespace):
        """Generator of the keys in a namespace."""
        return (d.name for d in (self.directory / str(namespace)).iterdir())

    def delete_namespace(self, namespace):
        """Delete all files in ``namespace``"""
        from shutil import rmtree
        rmtree(str(self.directory / str(namespace)))

    def get_reader(self, namespace, key):
        try:
            return open(str(self.directory / str(namespace) / key), 'rb')
        except FileNotFoundError as e:
            raise KeyError(
                'Key not found: {} / {}'.format(namespace, key)) from e

    def put(self, namespace, metadata, bytes_io):
        outdir = self.directory / str(namespace)
        if not outdir.exists():
            outdir.mkdir()  # Create the namespace directory as needed
        outfile = outdir / metadata['md5']
        with open(str(outfile), mode='wb', buffering=MEGABYTE) as writer:
            while True:
                chunk = bytes_io.read(MEGABYTE)
                if chunk:
                    writer.write(chunk)
                else:
                    break
        assert outfile.lstat().st_size == metadata['length']

    def get_url(self, namespace, key, seconds=3600, https=False):
        """Return a Pyramid static URL.

        If you use another web framework, please override this method.
        """
        from pyramid.threadlocal import get_current_request
        return get_current_request().static_url(
            '/'.join((self.storage_path, str(namespace), key)))
