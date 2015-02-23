# -*- coding: utf-8 -*-

'''keepluggable resources (for Pyramid traversal)'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
# from pyramid.decorator import reify
# from keepluggable.actions import FilesAction


class BaseFilesResource(object):
    '''Base class for a Pyramid traversal resource representing a file store.

        Usually an application will store its files in a single S3 bucket,
        but there will be a need to namespace the files. This namespace
        will depend on the parent resources in the URL. Thus, subclasses
        must provide (maybe in the form of Python properties):

        - ``namespace``: A name for a namespace name that will contain files,
          such that a bucket will contain multiple namespaces.

        Here is an example implementation that simply returns an integer::

            @reify
            def namespace(self):
                return self.__parent__.model_instance.id

        Resources must also provide ``__name__`` and ``__parent__``. You can
        read more about this in the Pyramid docs.
        '''
    pass


class BaseFileResource(object):
    '''Base class for a Pyramid traversal resource representing a
        specific file. It also needs to provide ``namespace``.
        '''
    pass
