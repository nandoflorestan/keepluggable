# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class FileNotAllowed(Exception):
    """For when a file should not be stored. The message must explain why."""
