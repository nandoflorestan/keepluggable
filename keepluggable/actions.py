"""The base Action class."""

from bag.web.exceptions import Problem
import colander as c
from keepluggable.exceptions import FileNotAllowed


class BaseFilesAction(object):
    """Action class that coordinates the workflow.

    You are likely to need to subclass this.

    To enable this action, use this configuration::

        action.files = keepluggable.actions:BaseFilesAction


    **Configuration settings**

    - ``fls.max_file_size`` (int): the maximum file length, in bytes, that
      can be uploaded. When zero, the system does not have a maximum size.
    - ``fls.allow_empty_files`` (boolean): whether to allow zero-length
      files to be uploaded.
    - ``fls.update_schema`` (resource spec): Colander schema that validates
      metadata being updated. Without it, no validation is done, which is
      unsafe. So it is recommended that you implement a schema.
    """

    SETTINGS_PREFIX = 'fls.'

    class ConfigurationSchema(c.Schema):
        """Schema to validate configuration settings for BaseFilesAction."""

        max_file_size = c.SchemaNode(
            c.Int(), default=0, missing=0, validator=c.Range(min=0), doc="""\
The maximum file length, in bytes, that can be uploaded. \
When zero, the system does not have a maximum size.""")
        allow_empty_files = c.SchemaNode(
            c.Bool(), default=False, missing=False,
            doc="Whether to allow zero-length files to be uploaded.")

    def __init__(self, orchestrator, namespace):
        """Store orchestrator, namespace and the settings for this action."""
        self.orchestrator = orchestrator
        self.namespace = namespace
        self.settings = orchestrator.action_configuration

    def store_original_file(self, bytes_io, **metadata):
        """Point of entry into the workflow of storing a file.

        You can override this method in subclasses to change the steps
        since it is a sort of coordinator that calls one method for each step.

        The argument *bytes_io* is a file-like object with the payload.
        *metadata* is a dict with the information to be persisted in
        the metadata storage.
        """
        assert metadata['file_name']

        # This is not a derived file such as a resized image.
        metadata['version'] = 'original'

        self._compute_file_metadata(bytes_io, metadata)

        # Hook for subclasses to allow or forbid storing this file
        self._allow_storage_of(bytes_io, metadata)  # may raise FileNotAllowed

        # Hook for subclasses to deviate if the file already exists
        if hasattr(self, '_handle_upload_of_existing_file'):
            existing = self._file_already_exists(metadata)
            if existing:
                return self._handle_upload_of_existing_file(
                    bytes_io, metadata, existing)

        metadata['versions'] = self._store_versions(bytes_io, metadata)
        return self._complement(metadata)

    def _compute_file_metadata(self, bytes_io, metadata):
        """Override this method in subclasses to populate the file metadata."""
        self._guess_mime_type(bytes_io, metadata)
        self._compute_length(bytes_io, metadata)
        self._compute_md5(bytes_io, metadata)

    def _guess_mime_type(self, bytes_io, metadata):
        """Discover the MIME type from the uploaded file extension.

        Otherwise just keep the browser-provided mime_type (less reliable).

        If necessary, one might override this to use
        https://pypi.python.org/pypi/python-magic instead.
        """
        from mimetypes import guess_type
        typ = guess_type(metadata['file_name'])[0]
        if typ:
            metadata['mime_type'] = typ

    def _compute_length(self, bytes_io, metadata):
        from bag.streams import get_file_size
        metadata['length'] = get_file_size(bytes_io)

    def _compute_md5(self, bytes_io, metadata):
        from hashlib import md5
        two_megabytes = 1048576 * 2
        the_hash = md5()
        the_length = 0
        bytes_io.seek(0)
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

    def _allow_storage_of(self, bytes_io, metadata):
        """Override this method if you wish to abort storing some files.

        To abort, raise FileNotAllowed with a message explaining why.
        """
        maximum = self.settings['max_file_size']
        if maximum and metadata['length'] > maximum:
            raise FileNotAllowed(
                'The file is {} KB long and the maximum is {} KB.'.format(
                    int(metadata['length'] / 1024), int(maximum / 1024)))

        allow_empty = self.settings['allow_empty_files']
        if not allow_empty and metadata['length'] == 0:
            raise FileNotAllowed('The file is empty.')

    def _file_already_exists(self, metadata):
        """Return existing file with the same md5 in the namespace, or None."""
        return self.orchestrator.storage_metadata.get(
            namespace=self.namespace, key=metadata['md5'])

    def _store_versions(self, bytes_io, metadata):
        """In this base class, just call _store_file().

        But any subclass will have a complex workflow for storing versions.
        """
        return self._store_file(bytes_io, metadata)

    def _store_file(self, bytes_io, metadata):
        """Save the payload and the metadata on the 2 storage backends."""
        storage_file = self.orchestrator.storage_file
        storage_file.put(
            namespace=self.namespace, metadata=metadata, bytes_io=bytes_io)

        try:
            self._store_metadata(bytes_io, metadata)
        except:
            storage_file.delete(
                namespace=self.namespace, keys=(metadata['md5'],))
            raise
        return []  # no new versions are created in this case

    def _store_metadata(self, bytes_io, metadata):
        metadata['id'], metadata['is_new'] = \
            self.orchestrator.storage_metadata.put(
                namespace=self.namespace, metadata=metadata)

    def delete_file(self, key):
        """Delete a file's metadata and payload, including derived versions."""
        # Obtain the original file.
        sm = self.orchestrator.storage_metadata
        original = sm.get(namespace=self.namespace, key=key)
        if original is None:
            raise Problem('The file was not found.', status_int=404)

        # We are deleting the original and its versions.
        metadatas = [v for v in original['versions']]
        metadatas.append(original)

        # Delete the payloads
        self.orchestrator.storage_file.delete(self.namespace, metadatas)

        # Delete metadata entities
        # sm.delete_with_versions(self.namespace, original['md5'])
        for metadata in metadatas:
            sm.delete(self.namespace, metadata['md5'])

    def gen_originals(self, filters=None):
        """Yield the original files in this namespace.

        ...optionally with further filters.
        """
        # This implementation queries the DB once rather than thousands:
        universe = list(self.orchestrator.storage_metadata.gen_all(
            self.namespace, filters=filters))
        originals = {
            f['id']: f for f in universe if f['version'] == 'original'}
        for f in originals.values():
            f['versions'] = []
        for adict in universe:
            if adict['version'] == 'original':
                continue
            originals[adict['original_id']]['versions'].append(adict)
        for f in originals.values():
            f['versions'].sort(key=lambda fil: fil['image_width'])
        originals = originals.values()
        '''OLD IMPLEMENTATION: (The above is equivalent to this:)
        originals = self.orchestrator.storage_metadata.gen_originals(
            self.namespace, filters=filters)'''
        for fil in originals:
            yield self._complement(fil)

    def _complement(self, metadata):
        """Add the links for downloading the original file and its versions."""
        url = self.orchestrator.storage_file.get_url

        # Add the main *href*
        metadata['href'] = url(self.namespace, metadata)

        # Also add *href* for each version
        for version in metadata['versions']:
            version['href'] = url(self.namespace, version)
        return metadata

    def _validate_metadata_for_updating(self, adict):
        schema_cls = self.orchestrator.settings.resolve(
            'fls.update_schema', default=None)
        if schema_cls is not None:
            schema = schema_cls()
            adict = schema.deserialize(adict)
        return adict

    def update_metadata(self, id, adict):
        """Replace the metadata for key *id* with *adict*."""
        return self.orchestrator.storage_metadata.update(
            self.namespace, id, self._validate_metadata_for_updating(adict))
