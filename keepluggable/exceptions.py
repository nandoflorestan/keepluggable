# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class FileNotAllowed(Exception):
    """Thrown when a file shouldn't be stored. The message must explain why."""
