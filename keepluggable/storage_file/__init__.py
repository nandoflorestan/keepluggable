"""Strategies for storing file payloads."""

from abc import ABCMeta, abstractmethod
import mimetypes
from typing import BinaryIO, Sequence

from kerno.typing import DictStr

from keepluggable.orchestrator import Orchestrator


def get_extension(mime_type: str) -> str:
    """From a ``mime_type`` return a corresponding file extension, or empty."""
    extensions = sorted(mimetypes.guess_all_extensions(mime_type, strict=False))
    if not extensions:
        return ""
    extension = extensions[0]
    if extension == ".jfif":  # Suddenly with Ubuntu 22.04 we need this
        return ".jpe"
    return extension


class BasePayloadStorage(metaclass=ABCMeta):
    """Abstract base class ― formal interface for payload storage backends."""

    def __init__(self, orchestrator: Orchestrator) -> None:
        """Just store the orchestrator instance."""
        self.orchestrator = orchestrator

    @abstractmethod
    def put(self, namespace: str, metadata: DictStr, bytes_io: BinaryIO) -> None:
        """Store a file (``bytes_io``) inside ``namespace``."""
        raise NotImplementedError()

    @abstractmethod
    def get_reader(self, namespace: str, metadata: DictStr) -> BinaryIO:
        """Return an open "file" object from which the payload can be read.

        Otherwise, raise KeyError.
        """
        raise NotImplementedError()

    def _get_filename(self, metadata: DictStr) -> str:
        return metadata["md5"] + get_extension(metadata["mime_type"])

    @abstractmethod
    def get_url(
        self, namespace: str, metadata: DictStr, seconds: int = 3600, https: bool = True
    ) -> str:
        """Return a URL for a certain stored file."""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, namespace: str, metadatas: Sequence[DictStr]) -> None:
        """Delete many files within a namespace.

        metadatas is a Sequence, not just an Iterable, so we can len() it.
        """
        raise NotImplementedError()
