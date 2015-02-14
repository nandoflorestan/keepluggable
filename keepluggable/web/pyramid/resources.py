# -*- coding: utf-8 -*-

'''keepluggable resources (for Pyramid traversal)'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
# from pyramid.decorator import reify
# from keepluggable.actions import FilesAction


class BaseFilesResource(object):
    '''Base class for a Pyramid traversal resource representing a file store.

        Usually this file store will correspond, in S3 terms, to a
        single bucket, and the bucket identifier will depend on one
        of the parent resources in the URL. Thus, subclasses must provide
        (maybe in the form of Python properties) 2 instance variables:

        - **bucket_id**: The unqualified (e. g., without prefix) bucket
          identifier.

        Here is an example implementation which would return an integer::

            @reify
            def bucket_id(self):
                return self.__parent__.model_instance.id

        They must also provide __name__ and __parent__ as per Pyramid docs.
        '''
    pass
