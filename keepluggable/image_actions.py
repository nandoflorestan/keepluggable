"""An Action class that deals with images."""

from copy import copy
from io import BytesIO
from typing import Any, BinaryIO, Dict, List, Union

from bag.text import strip_lower_preparer, strip_preparer
import colander as c

# import imghdr  # imghdr.what(file)
from kerno.typing import DictStr
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener

from keepluggable.actions import BaseFilesAction
from keepluggable.exceptions import FileNotAllowed
from keepluggable.orchestrator import Orchestrator

register_heif_opener()  # and now Pillow can read the HEIC format.


def _image_format_validator(node, value: str):
    if value not in ("png", "jpeg", "gif"):
        raise c.Invalid(node, f"Unknown image format: {value}")
    return value


class ImageVersionConfig(c.MappingSchema):
    """A part of the configuration."""

    format = c.SchemaNode(
        c.String(), preparer=strip_lower_preparer, validator=_image_format_validator
    )
    height = c.SchemaNode(c.Int(), validator=c.Range(min=1))
    width = c.SchemaNode(c.Int(), validator=c.Range(min=1))
    name = c.SchemaNode(c.String(), preparer=strip_preparer, validator=c.Length(min=1))

    @classmethod
    def from_str(cls, line: str) -> DictStr:
        """From a configuration line, return a config dict."""
        parts = line.split()
        assert len(parts) == 4, f'The configuration line "{line}" should have 4 parts'
        return cls().deserialize(
            {
                "format": parts[0],
                "width": parts[1],
                "height": parts[2],
                "name": parts[3],
            }
        )


class ImageAction(BaseFilesAction):
    """A specialized Action class that deals with images.

    It converts formats, rotates and resizes images etc.

    To enable this action, use this configuration::

        cls_action = keepluggable.image_actions.ImageAction

    It inherits from BaseFilesAction, so read its documentation too.


    **Installing Pillow**

    To use this action, you need to install the Pillow imaging library::

        sudo apt-get install libjpeg-dev zlib1g-dev libfreetype6-dev
        # Create these links. If they already exist, remove and readd them:
        sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib
        sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib
        sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib
        pip install Pillow

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

    - ``upload_must_be_img``: a boolean; if True, uploads will only be
      accepted if they are image files. The default for this setting is False.
    - ``store_original``: a boolean; if False, the original upload will
      not have its payload stored. The metadata is always stored in an effort
      to recognize repeated uploads of the same file. The default for this
      setting is True.
    - ``versions``: a list of image versions in the form
      "format max-width max-height name"
    - ``versions_quality`` (integer): the quality parameter to be passed
      to the Pillow JPEG encoder. The default is 90.

    Here is an example configuration::

        [keepluggable_page_images]
        # (...)
        store_original = False
        versions =
            jpeg 3840 2160 4k
            jpeg 1920 1920 hd
            jpeg  960  960 half
            jpeg  480  480 quarter
            jpeg  240  240 vignette
        versions_quality = 90
    """

    EXIF_TAGS = {v: k for (k, v) in ExifTags.TAGS.items()}  # str to int map
    EXIF_ROTATION_FIX = {1: 0, 8: 90, 3: 180, 6: 270}

    class Config(BaseFilesAction.Config):
        """Validated configuration for ``ImageAction``."""

        upload_must_be_img = c.SchemaNode(c.Bool(), missing=False)
        store_original = c.SchemaNode(c.Bool(), missing=True)
        versions_quality = c.SchemaNode(c.Int(), missing=90)

    @classmethod
    def get_config(cls, settings: DictStr) -> DictStr:
        """Image versions are a complex string in configuration; parse them.

        This gets called by the orchestrator at startup.
        Return the entire action configuration dictionary.
        """
        value = settings["versions"]
        if not isinstance(value, str):
            return value

        # Convert str to validated dict
        versions: List[DictStr] = []
        for line in value.split("\n"):
            line = line.strip()
            if not line:  # Ignore an empty line
                continue
            versions.append(ImageVersionConfig.from_str(line))
        # We want to process image versions from smaller to bigger:
        versions.sort(key=lambda d: d["width"])

        config: DictStr = cls.Config().deserialize(settings)
        config["versions"] = versions
        return config

    def _img_from_stream(
        self,
        bytes_io: BinaryIO,
        metadata: Dict[str, Any],
    ) -> Image:
        try:
            img = Image.open(bytes_io)
        except OSError:
            raise FileNotAllowed(
                'Unable to store the image "{}" because '
                "the server is unable to identify the image format.".format(
                    metadata["file_name"]
                )
            )
        img.bytes_io = bytes_io
        return img

    def _rotate_exif_orientation(self, img: Image) -> Image:
        """Rotate the image according to metadata in the payload.

        Some cameras do not rotate the image, they just add orientation
        metadata to the file, so we rotate it here.
        """
        if not hasattr(img, "_getexif"):
            return img  # PIL.PngImagePlugin.PngImageFile apparently lacks EXIF
        tags = img._getexif()
        if tags is None:
            return img
        orientation = tags.get(self.EXIF_TAGS["Orientation"])
        if orientation is None:
            return img
        degrees = self.EXIF_ROTATION_FIX.get(orientation)
        rotated = img.rotate(degrees, expand=True) if degrees else img
        return rotated

    def _store_versions(
        self,
        bytes_io: BinaryIO,
        metadata: Dict[str, Any],
        repo: Any,
    ) -> None:
        # We override this method to deal with images.
        is_image = metadata["mime_type"].startswith("image")
        if not is_image:
            if self.config["upload_must_be_img"]:
                raise FileNotAllowed(
                    'The file name "{}" lacks a supported image extension, '
                    "so it was not stored.".format(metadata["file_name"])
                )
            else:
                super()._store_versions(bytes_io, metadata, repo)
                return

        # # If you need to load the image after verify(), must reopen it
        # bytes_io.seek(0)
        original = self._img_from_stream(bytes_io, metadata)  # may raise
        original = self._rotate_exif_orientation(original)

        # Probably don't need to verify() the image since we are loading it
        # original.verify()  # What does this raise?
        self._copy_img(original, metadata)  # Try to raise before storing

        #  No exceptions were raised,  so store the original file
        metadata["image_width"], metadata["image_height"] = original.size
        if self.config["store_original"]:  # Optionally store original payload
            self._store_file(bytes_io, metadata, repo)
        else:  # Always store original metadata
            self._store_metadata(bytes_io, metadata)

        # There is no point in enlarging an uploaded image, but some
        # configured sizes might be larger. We want to create only the
        # sizes smaller than the uploaded image, plus one (the original size).
        largest_version_created_so_far = 0
        original_area = original.size[0] * original.size[1]
        new_versions = []
        for version_config in self.config["versions"]:
            current_area = version_config["width"] * version_config["height"]
            if largest_version_created_so_far <= original_area:
                # Do it
                new_versions.append(
                    self._store_img_version(  # may raise
                        original, metadata, version_config, repo
                    )
                )
                largest_version_created_so_far = current_area
        metadata["versions"] = new_versions

    def _store_img_version(
        self,
        original: Image,
        original_metadata: Dict[str, Any],
        version_config: ImageVersionConfig,
        repo: Any,
    ) -> Dict[str, Any]:
        metadata = copy(original_metadata)
        metadata["version"] = version_config["name"]
        metadata["original_id"] = original_metadata["id"]
        del metadata["id"]

        img = self._convert_img(original, metadata, version_config)

        # Store the new metadata and the new payload
        self._store_file(img.stream, metadata, repo)

        return metadata

    def _copy_img(
        self,
        original: Image,
        metadata: Dict[str, Any],
        alpha: bool = True,
    ) -> Image:
        mode = "RGBA" if alpha else "RGB"
        try:
            return original.convert(mode)  # Create a copy
        except OSError:
            raise FileNotAllowed(
                'Unable to store the image "{}" because '
                "the server is unable to convert it.".format(metadata["file_name"])
            )

    def _convert_img(
        self,
        original: Image,
        metadata: Dict[str, Any],
        version_config: DictStr,
        resample=Image.LANCZOS,
    ) -> Image:
        """Return a new image, converted from ``original``.

        Do it using ``version_config`` and setting ``metadata``.
        """
        fmt = version_config["format"]

        # Resize, keeping the aspect ratio:
        img = self._copy_img(original, metadata, alpha=fmt != "jpeg")
        img.thumbnail((version_config["width"], version_config["height"]), resample)

        stream = BytesIO()
        img.save(
            stream,
            format=fmt.upper(),
            quality=self.config["versions_quality"],
            optimize=1,
        )
        img.stream = stream  # so we can recover it elsewhere

        # Fill in the metadata
        metadata["mime_type"] = "image/" + fmt
        metadata["image_width"], metadata["image_height"] = img.size
        self._compute_length(stream, metadata)
        self._compute_md5(stream, metadata)

        return img

    def _complement(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Omit the main *href* if we are not storing original images."""
        metadata = super()._complement(metadata)
        # Add main *href* if we are storing original images or if not image
        if metadata.get("image_width") and not self.config["store_original"]:
            del metadata["href"]
        return metadata
