# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
# import imghdr  # imghdr.what(file)
from copy import copy
from io import BytesIO
from PIL import Image, ExifTags
from bag.settings import asbool
from .exceptions import FileNotAllowed
from .actions import BaseFilesAction


class ImageAction(BaseFilesAction):
    """Actions that involve images, such as converting formats, resizing etc.

    To enable this action, use this configuration::

        action.files = keepluggable.image_actions:ImageAction

    It inherits from BaseFilesAction, whose docstring you should read too.


    **Installing Pillow**

    To use this action, you need to install the Pillow imaging library::

        sudo apt-get install libjpeg-dev zlib1g-dev libfreetype6-dev
        # Create these links. If they already exist, remove them and readd them:
        sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib
        sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib
        sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib
        easy_install -UZ Pillow

    Pay attention to the desired supported formats near the end of the output::

        *** TKINTER support not available
        --- JPEG support available
        *** OPENJPEG (JPEG2000) support not available
        --- ZLIB (PNG/ZIP) support available
        *** LIBTIFF support not available
        --- FREETYPE2 support available
        *** LITTLECMS2 support not available
        *** WEBP support not available
        *** WEBPMUX support not available


    **Configuration settings**

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
    """

    EXIF_TAGS = {v: k for (k, v) in ExifTags.TAGS.items()}  # str to int map

    EXIF_ROTATION_FIX = {1: 0, 8: 90, 3: 180, 6: 270}

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

    def _img_from_stream(self, bytes_io, metadata):
        try:
            img = Image.open(bytes_io)
        except OSError:
            raise FileNotAllowed(
                'Unable to store the image "{}" because '
                'the server is unable to identify the image format.'.format(
                    metadata['file_name']))
        img.bytes_io = bytes_io
        return img

    def _rotate_exif_orientation(self, img):
        """Rotate the image if necessary.

        Some cameras do not rotate the image, they just add orientation
        metadata to the file, so we rotate it here.
        """
        if not hasattr(img, '_getexif'):
            return img  # PIL.PngImagePlugin.PngImageFile apparently lacks EXIF
        tags = img._getexif()
        if tags is None:
            return img
        orientation = tags.get(self.EXIF_TAGS['Orientation'])
        if orientation is None:
            return img
        degrees = self.EXIF_ROTATION_FIX.get(orientation)
        return img.rotate(degrees) if degrees else img

    def _store_versions(self, bytes_io, metadata):
        # We override this method to deal with images.
        is_image = metadata['mime_type'].startswith('image')
        if not is_image:
            return self._store_file(bytes_io, metadata)  # from superclass

        # Probably don't need to verify the image since we are loading it
        # original = self._img_from_stream(bytes_io)
        # original.verify()  # TODO What does this raise?

        # # If you need to load the image after verify(), must reopen it
        # bytes_io.seek(0)
        original = self._img_from_stream(bytes_io, metadata)  # may raise
        original = self._rotate_exif_orientation(original)
        self._copy_img(original, metadata)  # Try to raise before storing

        #  No exceptions were raised,  so store the original file
        metadata['image_format'] = original.format
        metadata['image_width'], metadata['image_height'] = original.size
        if self.store_original:  # Optionally store original payload
            self._store_file(bytes_io, metadata)
        else:                        # Always store original metadata
            self._store_metadata(bytes_io, metadata)

        # There is no point in enlarging an uploaded image, but some
        # configured sizes might be larger. We want to create only the
        # sizes smaller than the uploaded image, plus one (the original size).
        largest_version_created_so_far = 0
        original_area = original.size[0] * original.size[1]
        metadatas = []
        for version_config in self.versions:
            current_area = version_config['width'] * version_config['height']
            if largest_version_created_so_far <= original_area:
                # Do it
                metadatas.append(self._store_img_version(  # may raise
                    original, metadata, version_config))
                largest_version_created_so_far = current_area

        return metadatas  # of the versions just created

    def _store_img_version(self, original, original_metadata, version_config):
        metadata = copy(original_metadata)
        metadata['version'] = version_config['name']
        metadata['original_id'] = original_metadata['id']
        del metadata['id']

        img = self._convert_img(original, metadata, version_config)

        # Store the new metadata and the new payload
        self._store_file(img.stream, metadata)

        return metadata

    def _copy_img(self, original, metadata):
        try:
            # if original.mode == 'RGBA':
            #     background = Image.new("RGB", original.size, (255, 255, 255))
            #     # 3 is the alpha channel:
            #     background.paste(original, mask=original.split()[3])
            #     return background
            # else:
            return original.convert('RGB')  # Creates a copy
        except OSError as e:
            raise FileNotAllowed(
                'Unable to store the image "{}" because '
                'the server is unable to convert it.'.format(
                    metadata['file_name']))

    def _convert_img(self, original, metadata, version_config):
        """Return a new image, converted from ``original``.

        ...using ``version_config`` and setting ``metadata``.
        """
        fmt = version_config['format']
        assert fmt in ('PNG', 'JPEG', 'GIF'), 'Unknown format {}'.format(fmt)
        img = self._copy_img(original, metadata)

        # Resize, keeping the aspect ratio:
        img.thumbnail((version_config['width'], version_config['height']))

        stream = BytesIO()
        img.save(stream, format=fmt, quality=self.quality, optimize=1)
        img.stream = stream  # so we can recover it elsewhere

        # Fill in the metadata
        metadata['mime_type'] = 'image/' + fmt
        metadata['image_format'] = fmt
        metadata['image_width'], metadata['image_height'] = img.size
        self._compute_length(stream, metadata)
        self._compute_md5(stream, metadata)

        return img

    def _complement(self, fil):
        """Omit the main *href* if we are not storing original images."""
        url = self.orchestrator.storage_file.get_url

        # Add main *href* if we are storing original images or if not image
        if fil.get('image_width') is None or self.store_original:
            fil['href'] = url(self.namespace, fil['md5'])

        # Also add *href* for each version
        for version in fil['versions']:
            version['href'] = url(self.namespace, version['md5'])
        return fil
