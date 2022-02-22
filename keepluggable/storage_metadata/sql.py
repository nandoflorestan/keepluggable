"""Component that stores file metadata in a relational database."""

from typing import Generator, Generic, List, Optional, TypeVar

from bag.sqlalchemy.tricks import ID, MinimalBase, now_column
from bag.web.exceptions import Problem
import colander as c
from kerno.repository.sqlalchemy import Query
from kerno.typing import DictStr
from kerno.web.to_dict import reuse_dict, to_dict
from sqlalchemy import Column
from sqlalchemy.orm import object_session
from sqlalchemy.types import Integer, Unicode

from keepluggable.orchestrator import Orchestrator


class BaseFile(ID, MinimalBase):
    """Base mixin class for a model that represents file metadata.

    The file MAY be an image.
    """

    # id = Primary key that exists because we inherit from ID
    md5 = Column(
        Unicode(32),
        nullable=False,
        doc="hashlib.md5(file_content).hexdigest()",
    )
    file_name = Column(
        Unicode(300),
        doc="Name of the original uploaded file, including extension",
    )
    length = Column(Integer, nullable=False, doc="File size in bytes")
    created = now_column()  # Stores the moment the instance is created
    mime_type = Column(Unicode(255), doc='MIME type; e.g. "image/jpeg"')
    # http://stackoverflow.com/questions/643690/maximum-mimetype-length-when-storing-type-in-db
    image_width = Column(Integer, doc="Image width in pixels")
    image_height = Column(Integer, doc="Image height in pixels")
    version = Column(Unicode(20), default="original")
    versions: List["BaseFile"]  # must be implemented in subclasses

    @property
    def aspect_ratio(self):
        """self.image_width / self.image_height."""
        return self.image_width / self.image_height

    @property
    def is_the_original(self):
        """self.original_id is None."""
        return self.original_id is None

    def get_original(self, sas):
        """Return the file this instance is derived from."""
        return sas.query(type(self)).get(self.original_id)

    def q_versions(self, sas=None, order_by="image_width"):  # TODO move
        """Query that returns files derived from this instance."""
        sas = sas or object_session(self)
        return sas.query(type(self)).filter_by(original_id=self.id).order_by(order_by)

    def __repr__(self):
        return '<{} #{} "{}" {}>'.format(
            type(self).__name__, self.id, self.file_name, self.version
        )


class StorageConfigSchema(c.Schema):
    """Validated configuration for ``SQLAlchemyMetadataStorage``.

    - ``metadata_model_cls`` must point to a certain model class to store
      the file metadata.
    - ``sql_session`` should point to a scoped session global variable.
      But instead of using this setting, you may override the
      ``SQLAlchemyMetadataStorage._get_session()`` method.
    """

    metadata_model_cls = c.SchemaNode(c.GlobalObject(package=None))
    sql_session = c.SchemaNode(c.GlobalObject(package=None), missing=None)


TFile = TypeVar("TFile", bound=BaseFile)


class SQLAlchemyMetadataStorage(Generic[TFile]):
    """File metadata storage backend base class using SQLAlchemy.

    This class certainly needs to be subclassed for your specific use case.
    You must examine the source code and override methods as necessary.
    The most important reason for this is that each application will need
    to namespace the stored files differently.

    **Creating your File model class**

    Your File model class must inherit from the BaseFile mixin class that
    we provide. Here is an example in which files are separated by user::

        from bag import fk_rel
        from keepluggable.storage_metadata.sql import (
            BaseFile, SQLAlchemyMetadataStorage)
        from sqlalchemy import Column, UniqueConstraint
        from sqlalchemy.types import Unicode

        from myapp.db import Base
        from myapp.modules.user.models import User


        class File(Base, BaseFile):
            __table_args__ = (
                UniqueConstraint('user_id', 'md5', name='file_user_md5_key'),
                {})

            # You can add any columns for information entered by the user:
            description = Column(Unicode(320), nullable=False, default='')
            # title = Column(Unicode(80), nullable=False)
            # alt

            # Relationships
            user_id, user = fk_rel(User, backref='files')

            @property  # Your File model must define a "namespace" property.
            def namespace(self):  # In this example a user has her own files.
                return str(self.user_id)

        # Create a self-referential foreign key and relationship so that
        # a file can point to its original version:
        File.original_id, File.versions = fk_rel(File, nullable=True)
        # When original_id is null, this is the original file.
    """

    def __init__(self, orchestrator: Orchestrator) -> None:
        """Read settings and ensure a SQLAlchemy session can be obtained."""
        self.orchestrator = orchestrator
        self.config = StorageConfigSchema().deserialize(
            self.orchestrator.config["settings"]
        )

        # Get a session at startup just to make sure it is configured
        assert self._get_session() is not None

    def _get_session(self):
        """Return the SQLAlchemy session."""
        return self.config["sql_session"]

    def put(
        self,
        namespace: str,
        metadata: DictStr,
        sas=None,
    ) -> DictStr:
        """Create or update a file corresponding to the given ``metadata``.

        This method returns a 2-tuple containing the ID of the entity
        and a boolean saying whether the entity is new or existing.

        Instead of overriding this method, it is probably better for
        you to override the methods it calls.
        """
        sas = sas or self._get_session()
        entity: Optional[TFile] = self._query(
            namespace, md5=metadata["md5"], sas=sas
        ).first()
        if entity is None:
            entity = self._instantiate(namespace, metadata, sas=sas)
            sas.add(entity)
        else:
            self._update(namespace, metadata, entity, sas=sas)
        sas.flush()
        metadata["id"] = entity.id
        return metadata

    def _query(
        self,
        namespace: str,
        md5: str = "",
        filters=None,
        what=None,
        sas=None,
    ) -> Query[TFile]:
        """Override this to search for an existing file.

        You probably need to do something with the ``namespace``.
        """
        sas = sas or self._get_session()
        q = sas.query(what or self.config["metadata_model_cls"])
        if md5:
            q = q.filter_by(md5=md5)
        if filters is not None:
            q = q.filter_by(**filters)
        return q

    def _instantiate(
        self,
        namespace: str,
        metadata: DictStr,
        sas=None,
    ) -> TFile:
        """Return an instance of the file model.

        Override this to add or delete arguments on the constructor call.
        You probably need to do something with the ``namespace``.
        """
        return self.config["metadata_model_cls"](**metadata)

    def _update(
        self,
        namespace: str,
        metadata: DictStr,
        entity,
        sas=None,
    ) -> TFile:
        """Update the metadata of an existing entity.

        You might need to override and do something with the ``namespace``.
        """
        for key, value in metadata.items():
            setattr(entity, key, value)
        sas.flush()
        return entity

    def update(
        self,
        namespace: str,
        id,
        metadata: DictStr,
        sas=None,
    ) -> DictStr:
        """Update a file metadata. It must exist in the database."""
        sas = sas or self._get_session()
        entity: Optional[TFile] = sas.query(self.config["metadata_model_cls"]).get(id)
        if entity is None:
            raise Problem(
                error_title="That file does not exist.",
                error_msg="File #{} does not exist in namespace {}. "
                "You may need to refresh.".format(id, namespace),
            )
        entity = self._update(namespace, metadata, entity, sas=sas)
        return to_dict(entity)

    def gen_originals(
        self, namespace: str, filters=None, sas=None
    ) -> Generator[DictStr, None, None]:
        """Generate original files (not derived versions)."""
        sas = sas or self._get_session()
        filters = {} if filters is None else filters
        filters["version"] = "original"
        for entity in self._query(namespace, filters=filters, sas=sas):
            yield to_dict(entity)

    def gen_all(
        self, namespace: str, filters=None, sas=None
    ) -> Generator[DictStr, None, None]:
        """Generate all the files (originals and derivations).

        Versions must be organized later -- this is a flat listing.
        """
        sas = sas or self._get_session()
        filters = {} if filters is None else filters
        for entity in self._query(namespace, filters=filters, sas=sas):
            yield to_dict(entity, versions=False)

    # Not currently used, except by the local storage
    def gen_keys(
        self, namespace: str, filters=None, sas=None
    ) -> Generator[str, None, None]:
        """Generate the keys in a namespace."""
        sas = sas or self._get_session()
        q = self._query(
            namespace,
            filters=filters,
            what=self.config["metadata_model_cls"].md5,  # type: ignore[attr-defined]
            sas=sas,
        )
        for tup in q:
            yield tup[0]

    def get(self, namespace: str, key: str, sas=None) -> DictStr:
        """Return a dict: the metadata of one file, or None if not found."""
        entity = self.get_entity(namespace, key, sas)
        return to_dict(entity) if entity else None

    def get_entity(self, namespace: str, key: str, sas=None) -> Optional[TFile]:
        """Return a model instance representing file metadata, or None."""
        return self._query(
            sas=sas or self._get_session(),
            namespace=namespace,
            md5=key,
        ).first()

    def delete_with_versions(self, namespace: str, key: str, sas=None) -> None:
        """Delete a file along with all its versions."""
        sas = sas or self._get_session()
        original = self._query(sas=sas, namespace=namespace, md5=key).one()
        for version in original.versions:
            sas.delete(version)
        sas.delete(original)

    def delete(self, namespace: str, key: str, sas=None) -> None:
        """Delete one file."""
        sas = sas or self._get_session()
        self._query(sas=sas, namespace=namespace, md5=key).delete()


@to_dict.register(obj=BaseFile, flavor="")
def file_to_dict(obj, flavor="", **kw):  # , versions=True
    """Convert instance to a dictionary, usually for JSON output."""
    amap = reuse_dict(obj=obj, sort=False, **kw)
    if kw.get("versions", True):
        amap["versions"] = [reuse_dict(obj=v, **kw) for v in obj.q_versions()]
    else:
        amap["versions"] = []
    return amap
