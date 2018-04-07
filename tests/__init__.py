"""Tests for the *keepluggable* library."""

from bag.sqlalchemy.tricks import fk_rel
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from keepluggable.storage_metadata.sql import BaseFile

Base = declarative_base(
    name="Base",
    # https://alembic.readthedocs.org/en/latest/naming.html
    # http://docs.sqlalchemy.org/en/rel_1_0/core/constraints.html#constraint-naming-conventions
    metadata=MetaData(naming_convention={
        "ix": 'ix_%(table_name)s_%(column_0_label)s',
        "uq": "%(table_name)s_%(column_0_name)s_key",
        "ck": "ck_%(table_name)s_%(column_0_name)s",
        # could be: "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
        "pk": "%(table_name)s_pkey",
    }),
    # cls=DBObj,
)


class File(Base, BaseFile):
    """Represents file metadata. The file MAY be an image."""


File.original_id, File.versions = fk_rel(File, nullable=True)
