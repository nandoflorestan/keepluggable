# -*- coding: utf-8 -*-

'''Base class for payload storage backends'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class BasePayloadStorage(object):
    def get_reader(self, namespace, key):
        '''Returns an open "file" object from which the payload can be read.
            Otherwise, raises KeyError.
            '''
        raise NotImplementedError()
