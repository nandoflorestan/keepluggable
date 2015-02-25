# -*- coding: utf-8 -*-

'''Pyramid calls its controllers "views".'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from bag.web.pyramid.views import ajax_view, get_json_or_raise
from pyramid.response import Response
from pyramid.view import view_config
from keepluggable.exceptions import FileNotAllowed
from . import _
from .resources import BaseFilesResource, BaseFileResource

# TODO: Apply decorators only in *includeme* and according to configuration


@view_config(context=BaseFilesResource, permission='kp_view_files',
             request_method='GET', renderer='json')
def list_files(context, request):
    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)
    return {'items': list(action.gen_originals(filters=context.filters))}


@view_config(context=BaseFilesResource, permission='kp_upload',
             request_method='POST', renderer='json')
# @csrf
def upload_multiple_files(context, request):
    '''The response contains **items**, an array containing either
        the metadata for each accepted file, or details of upload failure.
        Each failure will have "upload_failed": true.
        You can test failures by uploading zero-length files.
        The order of the *items* is the same as the uploaded *files*.
        '''
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

    items = []
    for fieldStorage in files:
        # encoding = fieldStorage.encoding
        try:
            metadata = action.store_original_file(
                bytes_io=fieldStorage.file, file_name=fieldStorage.filename,
                mime_type=fieldStorage.type, **other_posted_data)
            items.append(metadata)
        except FileNotAllowed as e:
            items.append({
                'upload_failed': True,
                'error_type': '"{}" was not stored. '.format(
                    fieldStorage.filename),
                'error_msg': str(e),
                'file_name': fieldStorage.filename,
                'mime_type': fieldStorage.type,
                })
    return {'items': items}


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


@view_config(context=BaseFileResource, name='metadata', #permission='kp_upload',
             accept='application/json', request_method='PUT', renderer='json')
@ajax_view
def update_metadata(context, request):
    adict = get_json_or_raise(request)
    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)
    return action.update_metadata(context.__name__, adict)
    # curl -i -H 'Content-Type: application/json' -H 'Accept: application/json' -X PUT -d '{"description": "Super knife", "asset_id": 1, "room_id": null, "user_id": 2}' http://localhost:6543/divisions/1/files/1/@@metadata
