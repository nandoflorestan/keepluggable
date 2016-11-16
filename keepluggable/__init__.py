# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from bag.settings import resolve  # TODO Replace
REQUIRED = object()


def read_setting(settings, key, default=REQUIRED):
    if default is REQUIRED:
        try:
            return settings[key]
        except KeyError:
            raise RuntimeError('The config file does not contain a "{}" entry '
                               'in its [keepluggable] section.'.format(key))
    else:
        return settings.get(key, default)


def resolve_setting(settings, key, default=REQUIRED):
    resource_spec = read_setting(settings, key, default)
    return None if resource_spec is None else resolve(resource_spec)
