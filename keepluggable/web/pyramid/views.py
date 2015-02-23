# -*- coding: utf-8 -*-

'''Pyramid calls its controllers "views".'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from bag.web.pyramid.views import ajax_view
from pyramid.response import Response
from pyramid.view import view_config
from keepluggable.exceptions import FileNotAllowed
from . import _
from .resources import BaseFilesResource, BaseFileResource


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


@view_config(context=BaseFileResource, permission='kp_upload',
             request_method='DELETE')
# @csrf
@ajax_view
def delete_file_and_its_versions(context, request):
    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)
    key_to_delete = context.__name__
    action.delete_file(key_to_delete)
    return Response(status_int=204)  # No content
