# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class BasePayloadStorage(object):
    """Base class for payload storage backends."""

    def __init__(self, orchestrator):
        """The constructor just stores the orchestrator instance."""
        self.orchestrator = orchestrator

    def get_reader(self, namespace, metadata):
        """Return an open "file" object from which the payload can be read.

        Otherwise, raise KeyError.
        """
        raise NotImplementedError()
