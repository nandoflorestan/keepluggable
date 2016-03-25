# -*- coding: utf-8 -*-

'''Pyramid calls its controllers "views".'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from bag.web.exceptions import Problem
from bag.web.pyramid.views import ajax_view, get_json_or_raise
from bag.web.pyramid.angular_csrf import csrf
from pyramid.response import Response
from keepluggable.exceptions import FileNotAllowed
from . import _
from .resources import BaseFilesResource, BaseFileResource


def list_files(context, request):
    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)
    return {'items': list(action.gen_originals(filters=context.filters))}
    # curl -i -H 'Accept: application/json' http://localhost:6543/d/1/files


@ajax_view
def upload_single_file(context, request):
    '''When happy, returns the uploaded file metadata as JSON.'''
    fieldStorage = request.POST.getone('file')
    if not fieldStorage.bytes_read:
        raise Problem(
            _('The server did not receive an uploaded file.'),
            error_title=_('Empty POST'),
            )

    other_posted_data = dict(request.POST)  # a copy
    del other_posted_data['file']

    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)

    # encoding = fieldStorage.encoding
    try:
        return action.store_original_file(
            bytes_io=fieldStorage.file, file_name=fieldStorage.filename,
            mime_type=fieldStorage.type, **other_posted_data)
    except (OSError, FileNotAllowed) as e:
        raise Problem(
            str(e),
            error_title='"{}" was not stored. '.format(
                fieldStorage.filename),
            file_name=fieldStorage.filename,
            mime_type=fieldStorage.type,
            )


def upload_multiple_files(context, request):
    '''The response has **items**, an array in which each element is either
        the metadata for an accepted file, or details of upload failure.
        Each failure will have ``"upload_failed": true``.
        You can test failures by uploading zero-length files.
        The order in the ``items`` array is the same as the uploaded *files*.
        '''
    files = request.POST.getall('files')
    if not files:
        raise Problem(
            _('The server did not receive any uploaded files.'),
            error_title=_('Empty POST'),
            )

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
        except (OSError, FileNotAllowed) as e:
            items.append({
                'upload_failed': True,
                'error_title': '"{}" was not stored. '.format(
                    fieldStorage.filename),
                'error_msg': str(e),
                'file_name': fieldStorage.filename,
                'mime_type': fieldStorage.type,
                })
    return {'items': items}
    # Usually this sort of thing returns "201 Created" with an empty body and
    # an HTTP header containing the URL of the new resource::
    # Location: http://<domain>/division/42/docs/45829867
    # We don't do this because we support uploading multiple files.


@ajax_view
def delete_file_and_its_versions(context, request):
    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)
    key_to_delete = context.__name__
    action.delete_file(key_to_delete)
    return Response(status_int=204)  # No content


@ajax_view
def update_metadata(context, request):
    adict = get_json_or_raise(request)
    orchestrator = request.registry.settings['keepluggable']
    action = orchestrator.files_action_cls(orchestrator, context.namespace)
    return action.update_metadata(context.__name__, adict)
    # curl -i -H 'Content-Type: application/json' -H 'Accept: application/json' -X PUT -d '{"description": "Super knife", "asset_id": 1, "room_id": null, "user_id": 2}' http://localhost:6543/d/1/files/1/@@metadata


def register_pyramid_views(config, angular_csrf=False):
    config.add_view(
        view=csrf(list_files) if angular_csrf else list_files,
        context=BaseFilesResource, permission='kp_view_files',
        accept='application/json', request_method='GET', renderer='json')

    config.add_view(
        view=csrf(upload_single_file) if angular_csrf else upload_single_file,
        context=BaseFilesResource, name='single', permission='kp_upload',
        accept='application/json', request_method='POST', renderer='json')

    config.add_view(
        view=csrf(delete_file_and_its_versions) if angular_csrf
        else delete_file_and_its_versions,
        context=BaseFileResource, permission='kp_upload',
        request_method='DELETE')

    config.add_view(
        view=csrf(update_metadata) if angular_csrf else update_metadata,
        context=BaseFileResource, name='metadata', permission='kp_upload',
        accept='application/json', request_method='PUT', renderer='json')


def includeme(config):
    register_pyramid_views(config)
