# -*- coding: utf-8 -*-

'''Pyramid calls its controllers "views".'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pyramid.view import view_config
from keepluggable.exceptions import FileNotAllowed
from . import _
from .resources import BaseFilesResource


# POST to (for example) ../some/file_store/@@upload
@view_config(context=BaseFilesResource, permission='kp_upload',
             request_method='POST', renderer='json')
# @csrf
def upload_multiple_files(context, request):
    files = request.POST.getall('files')
    if not files:
        request.response.status_int = 400  # Bad request
        return dict(
            error_type=_('Empty POST'),
            error_msg=_('The server did not receive any uploaded files.'))

    other_posted_data = dict(request.POST)  # a copy
    del other_posted_data['files']

    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)

    ids = []
    failures = []
    for fieldStorage in files:
        # encoding = fieldStorage.encoding
        try:
            metadata = action.store_original_file(
                bytes_io=fieldStorage.file, file_name=fieldStorage.filename,
                mime_type=fieldStorage.type, **other_posted_data)
            ids.append(metadata['id'])
        except FileNotAllowed as e:
            failures.append(
                '"{}" was not stored. '.format(fieldStorage.filename) + str(e))
    return {'items': ids, 'failures': failures}
