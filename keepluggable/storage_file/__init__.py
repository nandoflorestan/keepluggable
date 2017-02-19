"""This namespace contains strategies for storing file payloads."""

from abc import ABCMeta, abstractmethod


class BasePayloadStorage(metaclass=ABCMeta):
    """Abstract base class ― formal interface for payload storage backends."""

    def __init__(self, orchestrator):
        """The constructor just stores the orchestrator instance."""
        self.orchestrator = orchestrator

    @abstractmethod
    def empty_bucket(self, bucket=None):
        """Delete all files in this storage."""
        raise NotImplementedError()

    @abstractmethod
    def put(self, namespace, metadata, bytes_io):
        """Store a file (``bytes_io``) inside ``namespace``."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def namespaces(self):
        """Generator of existing namespace names."""
        raise NotImplementedError()

    @abstractmethod
    def gen_keys(self, namespace):
        """Generator of the existing keys in a namespace."""
        raise NotImplementedError()

    @abstractmethod
    def get_reader(self, namespace, metadata):
        """Return an open "file" object from which the payload can be read.

        Otherwise, raise KeyError.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_url(self, namespace, metadata):
        """Return an URL for a certain stored file."""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, namespace, metadatas):
        """Delete many files within a namespace."""
        raise NotImplementedError()

    @abstractmethod
    def delete_namespace(self, namespace):
        """Delete all files in ``namespace``."""
        raise NotImplementedError()
