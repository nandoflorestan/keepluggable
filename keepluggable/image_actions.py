# -*- coding: utf-8 -*-

'''Actions that involve images, such as converting formats, resizing etc.
    go into ImageAction.

    To enable this action, use this configuration::

        action.files = keepluggable.image_actions:ImageAction

    It inherits from BaseFilesAction, whose docstring you should read too.

    Configuration settings
    ======================

    - ``img.store_original``: a boolean; if False, the original upload will
      not have its payload stored. The metadata is always stored in an effort
      to recognize repeated uploads of the same file. The default for this
      setting is True.
    - ``img.versions``: a list of image versions in the form
      "format max-width max-height name"
    - ``img.versions_quality`` (integer): the quality parameter to be passed
      to the Pillow JPEG encoder. The default is 90.

    Here is an example configuration::

        [keepluggable]
        # (...)
        img.store_original = False
        img.versions =
            jpeg 1920 1920 hd
            jpeg  960  960 half
            jpeg  480  480 quarter
            jpeg  240  240 vignette
            jpeg  160  160 thumb
        img.versions_quality = 90
    '''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
# import imghdr  # imghdr.what(file)
from copy import copy
from io import BytesIO
from PIL import Image
from bag import asbool
from .actions import BaseFilesAction


class ImageAction(BaseFilesAction):
    __doc__ = __doc__

    def __init__(self, *a, **kw):
        super(ImageAction, self).__init__(*a, **kw)

        # Read configuration
        self.store_original = asbool(self.orchestrator.settings.get(
            'img.store_original', True))
        self.quality = int(self.orchestrator.settings.get(
            'img.versions_quality', 90))
        versions = self.orchestrator.settings.get(
            'img.versions').strip().split('\n')
        self.versions = []
        for astring in versions:
            astring = astring.strip()
            parts = astring.split()
            assert len(parts) == 4, \
                'The configuration line "{}" should have 4 parts'.format(
                    astring)
            adict = {
                'format': parts[0].upper(),
                'width': int(parts[1]),
                'height': int(parts[2]),
                'name': parts[3],
                }
            self.versions.append(adict)

        # We want to process from smaller to bigger, so order versions by area:
        self.versions.sort(key=lambda d: d['width'] * d['height'])

    def _img_from_stream(self, bytes_io):
        img = Image.open(bytes_io)
        img.bytes_io = bytes_io
        return img

    def _store_versions(self, bytes_io, metadata):
        # We override this method to deal with images.
        is_image = metadata['mime_type'].startswith('image')
        if not is_image:
            return self._store_file(bytes_io, metadata)  # from superclass

        # Before anything else, ensure the image is not corrupt
        original = self._img_from_stream(bytes_io)
        original.verify()  # TODO Does this raise?
        # Because verify() erases .fp, we put it back:
        original.fp = bytes_io  # otherwise the img won't clone later!
        metadata['image_format'] = original.format
        metadata['image_width'], metadata['image_height'] = original.size

        if self.store_original:  # Optionally store original payload
            self._store_file(bytes_io, metadata)
        else:
            self._store_metadata(bytes_io, metadata)  # Always store metadata

        # There is no point in enlarging an uploaded image, but some
        # configured sizes might be larger. We want to create only the
        # sizes smaller than the uploaded image, plus one (the original size).
        largest_version_created_so_far = 0
        original_area = original.size[0] * original.size[1]
        for version_config in self.versions:
            current_area = version_config['width'] * version_config['height']
            if largest_version_created_so_far <= original_area:
                # Do it
                self._store_img_version(original, metadata, version_config)
                largest_version_created_so_far = current_area

    def _store_img_version(self, original, original_metadata, version_config):
        metadata = copy(original_metadata)
        metadata['version'] = version_config['name']
        metadata['original_id'] = original_metadata['id']
        del metadata['id']

        img = self._convert_img(original, metadata, version_config)

        # Store the new metadata and the new payload
        self._store_file(img.stream, metadata)

    def _convert_img(self, original, metadata, version_config):
        '''Return a new image, converted from ``original``, using
            ``version_config`` and setting ``metadata``.
            '''
        img = original.convert('RGB')  # Creates a copy
        # Resize, keeping the aspect ratio:
        img.thumbnail((version_config['width'], version_config['height']))

        stream = BytesIO()
        img.save(stream, format=version_config['format'],
                 quality=self.quality, optimize=1)
        img.stream = stream  # so we can recover it elsewhere

        # Fill in the metadata
        metadata['image_format'] = version_config['format']
        metadata['image_width'], metadata['image_height'] = img.size
        self._compute_length(stream, metadata)
        self._compute_md5(stream, metadata)

        return img
