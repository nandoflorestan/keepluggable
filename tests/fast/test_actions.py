"""Fast unit tests for keepluggable actions."""

from unittest import TestCase
from keepluggable.actions import BaseFilesAction


class TestActionConfig(TestCase):

    def _make_one(self, allow_empty_files):
        return BaseFilesAction.Config(
            max_file_size='0',
            cls_update_metadata_schema=None,
            allow_empty_files=allow_empty_files,
        )

    def test_boolean_from_text(self):
        config = self._make_one('True')
        assert config.max_file_size == 0
        assert config.cls_update_metadata_schema is None
        assert config.allow_empty_files is True
        config = self._make_one('true')
        assert config.allow_empty_files is True
        config = self._make_one('1')
        assert config.allow_empty_files is True
        config = self._make_one('False')
        assert config.allow_empty_files is False
        config = self._make_one('false')
        assert config.allow_empty_files is False
