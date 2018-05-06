"""Pyramid calls its controllers "views".

Views must be thin. They marshal data into *actions* that contain the actual
business logic ― which thus becomes reusable.
"""

from typing import Any, Dict

from bag.web.exceptions import Problem
from bag.web.pyramid.views import ajax_view, get_json_or_raise
from pyramid.response import Response

from keepluggable.exceptions import FileNotAllowed
from keepluggable.web.pyramid import _
from .resources import BaseFilesResource, BaseFileResource


def list_files(context, request):
    """Return a dict with an *items* list containing original files.

    Example request with the ``curl`` command::

        curl -i -H 'Accept: application/json' http://localhost:6543/d/1/files
    """
    return {'items': list(
        context.action.gen_originals(filters=context.filters))}


@ajax_view
def upload_single_file(context, request):
    """When happy, returns the uploaded file metadata as JSON."""
    fieldStorage = request.POST.getone('file')
    if not fieldStorage.bytes_read:
        raise Problem(
            _('The server did not receive an uploaded file.'),
            error_title=_('Empty POST'))

    other_posted_data = dict(request.POST)  # a copy
    del other_posted_data['file']

    try:
        return context.action.store_original_file(
            bytes_io=fieldStorage.file, file_name=fieldStorage.filename,
            mime_type=fieldStorage.type, **other_posted_data)
    except (OSError, FileNotAllowed) as e:
        raise Problem(
            str(e),
            error_title='"{}" was not stored. '.format(
                fieldStorage.filename),
            file_name=fieldStorage.filename,
            mime_type=fieldStorage.type)


def upload_multiple_files(context, request):
    """Store multiple uploads from the POST variable "files".

    The response has **items**, an array in which each element is either
    the metadata for an accepted file, or details of upload failure.
    Each failure will have ``"upload_failed": true``.
    You can test failures by uploading zero-length files.
    The order in the ``items`` array is the same as the uploaded *files*.
    """
    files = request.POST.getall('files')
    if not files:
        raise Problem(
            _('The server did not receive any uploaded files.'),
            error_title=_('Empty POST'))

    other_posted_data = dict(request.POST)  # a copy
    del other_posted_data['files']

    items = []
    for fieldStorage in files:
        # encoding = fieldStorage.encoding
        try:
            metadata = context.action.store_original_file(
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
    """Delete a file and its derived versions."""
    key_to_delete = context.__name__
    context.action.delete_file(key_to_delete)
    return Response(status_int=204)  # No content


@ajax_view
def update_metadata(context, request):
    """Store new metadata for an existing file.

    Example request using the ``curl`` command::

        curl -i -H 'Content-Type: application/json'
        -H 'Accept: application/json' -X PUT
        -d '{"description": "Super knife", "title": "A knife",
        "asset_ids": [1], "room_id": null}'
        http://localhost:6543/d/1/files/1/@@metadata
    """
    adict = get_json_or_raise(request)
    return context.action.update_metadata(context.__name__, adict)


def get_operations(base_url: str = '') -> Dict[str, Dict[str, Any]]:
    """Return a dict containing all information about our views and URLs."""
    return {
        'List files in storage': dict(
            url_templ='{}'.format(base_url),
            context=BaseFilesResource,
            permission='kp_view_files', accept='application/json',
            request_method='GET', renderer='json', view=list_files),
        'Upload a single file': dict(
            url_templ='{}/@@single'.format(base_url),
            context=BaseFilesResource, name='single', permission='kp_upload',
            accept='application/json', request_method='POST',
            renderer='json', view=upload_single_file),
        'Delete a file': dict(
            url_templ='{}/:md5'.format(base_url),
            context=BaseFileResource, permission='kp_upload',
            request_method='DELETE', view=delete_file_and_its_versions),
        'Update file metadata': dict(
            url_templ='{}/:file_id/@@metadata'.format(base_url),
            context=BaseFileResource, name='metadata', permission='kp_upload',
            accept='application/json', request_method='PUT',
            renderer='json', view=update_metadata),
    }


def register_pyramid_views(config, base_url=''):
    """Register keepluggable views with plain Pyramid."""
    for op in get_operations(base_url=base_url).values():
        view = op['view']
        config.add_view(
            view=view,
            context=op['context'], name=op.get('name'),
            permission=op['permission'], accept=op.get('accept'),
            request_method=op['request_method'], renderer=op.get('renderer'))


def register_operations_with_burla(ops, base_url=''):
    """More featureful registration of the views using ``bag.web.burla``."""
    for op_name, adict in get_operations(base_url=base_url).items():
        view = adict.pop('view')
        ops.op(op_name=op_name, section='Files', **adict)(view)


def includeme(config):
    """Pyramid integration."""
    register_pyramid_views(config)
