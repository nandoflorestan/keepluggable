# -*- coding: utf-8 -*-

'''Pyramid calls its controllers "views".'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pyramid.view import view_config
from .resources import BaseFilesResource


# POST to (for example) ../some/file_store/@@upload
@view_config(context=BaseFilesResource, permission='kp_upload',
             # accept='application/json',
             request_method='POST', renderer='json')
# @csrf
# @ajax_view
def upload_multiple_files(context, request):
    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.bucket_name)
    ids = []
    for fieldStorage in request.POST.getall('files'):
        # buffered_reader = fieldStorage.fp
        ids.append(action.store_original_file(
            bytes_io=fieldStorage.file, file_name=fieldStorage.filename,
            mimetype=fieldStorage.type, encoding=fieldStorage.encoding))
    return {'items': ids}