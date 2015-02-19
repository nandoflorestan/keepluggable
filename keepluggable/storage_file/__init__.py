# -*- coding: utf-8 -*-

'''Base class for payload storage backends'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class BasePayloadStorage(object):
    def clear(self):
        '''Remove all buckets'''
        for bucket in self.bucket_names:
            self.delete_bucket(bucket)
