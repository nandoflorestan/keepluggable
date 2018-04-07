"""Unit tests for keepluggable's BaseFile model mixin."""

from collections import OrderedDict
from datetime import datetime
from unittest import TestCase
from kerno.web.to_dict import to_dict
from .. import File


class TestBaseFile(TestCase):

    def _make_one(self, versions=1):
        kw = dict(
            file_name="back_orifice.exe",
            length=9999,
            created=datetime(2018, 4, 2),
            mime_type="image/jpeg",
            image_height=60,
            image_width=80,
        )
        original = File(
            id=1,
            md5='1234567890abcdef',
            version='original',
            **kw
        )
        for i in range(versions):
            original.versions.append(File(
                id=i,
                md5='1234567890abcdef' + str(i),
                version='small',
                **kw
            ))
        return original

    def test_repr(self):
        assert '<File #1 "back_orifice.exe" original>' == \
            repr(self._make_one())

    def test_to_dict_no_versions(self):
        assert to_dict(self._make_one(0), versions=False) == OrderedDict([
            ('id', 1),
            ('md5', '1234567890abcdef'),
            ('version', 'original'),
            ('file_name', 'back_orifice.exe'),
            ('length', 9999),
            ('created', '2018-04-02T00:00:00'),
            ('mime_type', 'image/jpeg'),
            ('image_height', 60),
            ('image_width', 80),
            ('versions', []),
        ])
