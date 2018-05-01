"""Strategies for storing file payloads."""

from abc import ABCMeta, abstractmethod
import mimetypes
from typing import Any, Dict, Sequence

from keepluggable.orchestrator import Orchestrator


class BasePayloadStorage(metaclass=ABCMeta):
    """Abstract base class ― formal interface for payload storage backends."""

    def __init__(self, orchestrator: Orchestrator) -> None:
        """Just store the orchestrator instance."""
        self.orchestrator = orchestrator

    @abstractmethod
    def put(self, namespace, metadata, bytes_io):
        """Store a file (``bytes_io``) inside ``namespace``."""
        raise NotImplementedError()

    @abstractmethod
    def get_reader(self, namespace, metadata):
        """Return an open "file" object from which the payload can be read.

        Otherwise, raise KeyError.
        """
        raise NotImplementedError()

    def _get_extension(self, metadata: Dict[str, Any]) -> str:
        extensions = sorted(mimetypes.guess_all_extensions(
            metadata['mime_type'], strict=False))
        return extensions[0] if extensions else ''

    def _get_filename(self, metadata: Dict[str, Any]) -> str:
        return metadata['md5'] + self._get_extension(metadata)

    @abstractmethod
    def get_url(
        self, namespace: str, metadata: Dict[str, Any], seconds: int = 3600,
        https: bool = True,
    ) -> str:
        """Return an URL for a certain stored file."""
        raise NotImplementedError()

    @abstractmethod
    def delete(
        self, namespace: str, metadatas: Sequence[Dict[str, Any]],
    ) -> None:
        """Delete many files within a namespace."""
        raise NotImplementedError()

    '''
    @abstractmethod
    def delete_namespace(self, namespace):
        """Delete all files in ``namespace``."""
        raise NotImplementedError()
    '''
