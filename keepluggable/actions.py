"""The base Action class."""

from typing import Any, BinaryIO, Dict, Iterable, Optional, TYPE_CHECKING

from bag.web.exceptions import Problem
from pydantic import conint, PyObject, Required, validator

from keepluggable import Pydantic, ZeroOrMore
from keepluggable.exceptions import FileNotAllowed
from keepluggable.orchestrator import Orchestrator


class BaseFilesAction:
    """Action class that coordinates the workflow.

    You are likely to need to subclass this.

    To enable this action, use this configuration::

        action_cls = keepluggable.actions:BaseFilesAction
    """

    def __init__(self, orchestrator: Orchestrator, namespace: str) -> None:
        """Instantiate an action for one request."""
        self.orchestrator = orchestrator
        self.namespace = namespace
        self.config = orchestrator.action_config

    class Config(Pydantic):
        """Validated configuration for BaseFilesAction.

        - ``max_file_size`` (int): the maximum file length, in bytes, that
          can be uploaded. When zero, the system does not have a maximum size.
        - ``allow_empty_files`` (boolean): whether to allow zero-length
          files to be uploaded.
        - ``cls_update_metadata_schema`` (dotted resource spec):
          Colander schema that validates metadata being updated.
          Without it, no validation is done, which is unsafe.
          So it is recommended that you implement a schema.
        """

        max_file_size: ZeroOrMore = 0
        allow_empty_files: bool = False
        cls_update_metadata_schema: Optional[PyObject] = None

    def store_original_file(
        self, bytes_io: BinaryIO, **metadata
    ) -> Dict[str, Any]:
        """Point of entry into the workflow of storing a file.

        You can override this method in subclasses to change the steps
        since it is a sort of coordinator that calls one method for each step.

        The argument *bytes_io* is a file-like object with the payload.
        *metadata* is a dict with the information to be persisted in
        the metadata storage.
        """
        assert metadata["file_name"]

        # This is not a derived file such as a resized image.
        metadata["version"] = "original"

        self._compute_file_metadata(bytes_io=bytes_io, metadata=metadata)

        # In the case of images, keepluggable can be configured to not store
        # the original, but it still must be checked for duplicates
        self._check_for_existing_file(bytes_io=bytes_io, metadata=metadata)

        # Hook for subclasses to allow or forbid storing this file
        # by raising FileNotAllowed
        self._allow_storage_of(bytes_io=bytes_io, metadata=metadata)

        self._store_versions(bytes_io=bytes_io, metadata=metadata)
        return self._complement(metadata)

    def _compute_file_metadata(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        """Override this method in subclasses to populate the file metadata."""
        self._guess_mime_type(bytes_io, metadata)
        self._compute_length(bytes_io, metadata)
        self._compute_md5(bytes_io, metadata)

    def _guess_mime_type(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        """Discover the MIME type from the uploaded file extension.

        Otherwise just keep the browser-provided mime_type (less reliable).

        If necessary, one might override this to use
        https://pypi.python.org/pypi/python-magic instead.
        """
        from mimetypes import guess_type

        typ = guess_type(metadata["file_name"])[0]
        if typ:
            metadata["mime_type"] = typ

    def _compute_length(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        from bag.streams import get_file_size

        metadata["length"] = get_file_size(bytes_io)

    def _compute_md5(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        from hashlib import md5

        two_megabytes = 1048576 * 2
        the_hash = md5()
        the_length = 0
        bytes_io.seek(0)
        while True:
            segment = bytes_io.read(two_megabytes)
            if segment == b"":
                break
            the_length += len(segment)
            the_hash.update(segment)
        metadata["md5"] = the_hash.hexdigest()
        previous_length = metadata.get("length")
        if previous_length is None:
            metadata["length"] = the_length
        else:
            assert previous_length == the_length, (
                "Bug? File lengths {}, {} "
                "don't match.".format(previous_length, the_length)
            )
        bytes_io.seek(0)  # ...so it can be read again

    def _allow_storage_of(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        """Override this method if you wish to abort storing some files.

        To abort, raise FileNotAllowed with a message explaining why.
        """
        maximum = self.config.max_file_size
        if maximum and metadata["length"] > maximum:
            raise FileNotAllowed(
                "The file is {} KB long and the maximum is {} KB.".format(
                    int(metadata["length"] / 1024), int(maximum / 1024)
                )
            )

        if not self.config.allow_empty_files and metadata["length"] == 0:
            raise FileNotAllowed("The file is empty.")

    def _store_versions(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        """In this base class, just call _store_file().

        But most subclasses will have a complex workflow for storing versions.
        """
        metadata["versions"] = []
        self._store_file(bytes_io, metadata)

    def _check_for_existing_file(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        # Hook for subclasses to deviate if the file already exists
        if hasattr(self, "_handle_upload_of_existing_file"):
            existing = self._file_already_exists(metadata)
            # print(existing, metadata['version'], metadata)
            # import ipdb; ipdb.set_trace() # TODO Remove debug
            if existing:
                self._handle_upload_of_existing_file(  # type: ignore
                    bytes_io=bytes_io, metadata=metadata, existing=existing,
                )
                # TODO We should roll back any versions stored in AWS
                # In fact, we should validate everything before sending any

    def _file_already_exists(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Return existing file with the same md5 in the namespace, or None."""
        return self.orchestrator.storage_metadata.get(
            namespace=self.namespace, key=metadata["md5"]
        )

    def _store_file(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        """Save the payload and the metadata on the 2 storage backends.

        The arguments contain either the file being uploaded, or the
        versions of it that we create (e. g. image sizes).

        But first we check for duplicates of the file being stored.
        """
        self._check_for_existing_file(bytes_io=bytes_io, metadata=metadata)

        storage_file = self.orchestrator.storage_file
        storage_file.put(
            namespace=self.namespace, metadata=metadata, bytes_io=bytes_io
        )

        try:
            self._store_metadata(bytes_io, metadata)
        except Exception:
            storage_file.delete(namespace=self.namespace, metadatas=[metadata])
            raise

    def _store_metadata(
        self, bytes_io: BinaryIO, metadata: Dict[str, Any],
    ) -> None:
        self.orchestrator.storage_metadata.put(
            namespace=self.namespace, metadata=metadata
        )

    def delete_file(self, key: str) -> None:
        """Delete a file's metadata and payload, including derived versions."""
        # Obtain the original file.
        sm = self.orchestrator.storage_metadata
        original = sm.get(namespace=self.namespace, key=key)
        if original is None:
            raise Problem("The file was not found.", status_int=404)

        # We are deleting the original and its versions.
        metadatas = [v for v in original["versions"]]
        metadatas.append(original)

        # Delete the payloads
        self.orchestrator.storage_file.delete(self.namespace, metadatas)

        # Delete metadata entities
        # sm.delete_with_versions(self.namespace, original['md5'])
        for metadata in metadatas:
            sm.delete(self.namespace, metadata["md5"])

    def gen_originals(self, filters=None) -> Iterable[Dict[str, Any]]:
        """Yield the original files in this namespace.

        ...optionally with further filters.
        """
        # This implementation queries the DB once rather than thousands:
        universe = list(
            self.orchestrator.storage_metadata.gen_all(
                self.namespace, filters=filters
            )
        )
        originals = {
            f["id"]: f for f in universe if f["version"] == "original"
        }
        for f in originals.values():
            f["versions"] = []
        for adict in universe:
            if adict["version"] == "original":
                continue
            originals[adict["original_id"]]["versions"].append(adict)
        for f in originals.values():
            f["versions"].sort(key=lambda fil: fil["image_width"])
        """OLD IMPLEMENTATION: (The above is equivalent to this:)
        originals = self.orchestrator.storage_metadata.gen_originals(
            self.namespace, filters=filters)"""
        for fil in originals.values():
            yield self._complement(fil)

    def _complement(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Add the links for downloading the original file and its versions."""
        url = self.orchestrator.storage_file.get_url

        # Add the main *href*
        metadata["href"] = url(self.namespace, metadata)

        # Also add *href* for each version
        for version in metadata["versions"]:
            version["href"] = url(self.namespace, version)
        return metadata

    def _validate_metadata_for_updating(
        self, adict: Dict[str, Any],
    ) -> Dict[str, Any]:
        cls_update_metadata_schema = self.config.cls_update_metadata_schema
        if cls_update_metadata_schema is not None:
            schema = cls_update_metadata_schema()
            adict = schema.deserialize(adict)
        return adict

    def update_metadata(
        self, id: int, adict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Replace the metadata for key *id* with *adict*."""
        return self._complement(
            self.orchestrator.storage_metadata.update(
                self.namespace,
                id,
                self._validate_metadata_for_updating(adict),
            ),
        )
