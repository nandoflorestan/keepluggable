# -*- coding: utf-8 -*-

'''keepluggable resources (for Pyramid traversal)'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
# from pyramid.decorator import reify
# from keepluggable.actions import FilesAction


class BaseFilesResource(object):
    '''Base class for a Pyramid traversal resource representing a file store.
        Subclasses must provide a **bucket_name** instance variable
        (maybe in the form of a Python property).

        They must also provide __name__ and __parent__ as per Pyramid docs.
        '''
    pass
