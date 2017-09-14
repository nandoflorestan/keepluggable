"""Component that stores file metadata in a relational database."""

from bag.sqlalchemy.tricks import ID, MinimalBase, now_column
from bag.web.exceptions import Problem
from sqlalchemy import Column
from sqlalchemy.types import Integer, Unicode


class SQLAlchemyMetadataStorage(object):
    """File metadata storage backend base class using SQLAlchemy.

    This class certainly needs to be subclassed for your specific use case.
    You must examine the source code and override methods as necessary.
    The most important reason for this is that each application will need
    to namespace the stored files differently.

    **Configuration settings**

    - ``sql.file_model_cls`` must point to a certain model class to store
      the file metadata.
    - ``sql.session`` should point to a scoped session global variable.
      But instead of using this setting, you may override the
      ``_get_session()`` method.

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

    def __init__(self, orchestrator):
        """Read settings and ensure a SQLAlchemy session can be obtained."""
        self.orchestrator = orchestrator

        self.file_model_cls = orchestrator.settings.resolve(
            'sql.file_model_cls')

        # Get a session at startup just to make sure it is configured
        self._get_session()

    def _get_session(self):
        """Return the SQLAlchemy session."""
        return self.orchestrator.settings.resolve('sql.session')

    def put(self, namespace, metadata, sas=None):
        """Create or update a file corresponding to the given ``metadata``.

        This method returns a 2-tuple containing the ID of the entity
        and a boolean saying whether the entity is new or existing.

        Instead of overriding this method, it is probably better for
        you to override the methods it calls.
        """
        sas = sas or self._get_session()
        entity = self._query(namespace, key=metadata['md5'], sas=sas).first()
        is_new = entity is None
        if is_new:
            is_new = metadata.pop('is_new', None)
            entity = self._instantiate(namespace, metadata, sas=sas)
            sas.add(entity)
            metadata['is_new'] = is_new
        else:
            self._update(namespace, metadata, entity, sas=sas)
        sas.flush()
        return entity.id, is_new

    def _query(self, namespace, key=None, filters=None, what=None, sas=None):
        """Override this to search for an existing file.

        You probably need to do something with the ``namespace``.
        """
        sas = sas or self._get_session()
        q = sas.query(what or self.file_model_cls)
        if key is not None:
            q = q.filter_by(md5=key)
        if filters is not None:
            q = q.filter_by(**filters)
        return q

    def _instantiate(self, namespace, metadata, sas=None):
        """Return an instance of the file model.

        Override this to add or delete arguments on the constructor call.
        You probably need to do something with the ``namespace``.
        """
        return self.file_model_cls(**metadata)

    def _update(self, namespace, metadata, entity, sas=None):
        """Update the metadata of an existing entity.

        You might need to override and do something with the ``namespace``.
        """
        for key, value in metadata.items():
            setattr(entity, key, value)

    def update(self, namespace, id, metadata, sas=None):
        """Update a file metadata. It must exist in the database."""
        sas = sas or self._get_session()
        # entity = self._query(namespace, key=key, sas=sas).one()
        # entity = self._query(namespace, sas=sas).get(id)
        entity = sas.query(self.file_model_cls).get(id)
        if entity is None:
            raise Problem(
                error_title="That file does not exist.",
                error_msg="File #{} does not exist in namespace {}. "
                "You may need to refresh.".format(id, namespace),
            )
        self._update(namespace, metadata, entity, sas=sas)
        sas.flush()
        return entity.to_dict(sas)

    def gen_originals(self, namespace, filters=None, sas=None):
        """Generate original files (not derived versions)."""
        sas = sas or self._get_session()
        filters = {} if filters is None else filters
        filters['version'] = 'original'
        for entity in self._query(namespace, filters=filters, sas=sas):
            yield entity.to_dict(sas)

    def gen_all(self, namespace, filters=None, sas=None):
        """Generate all the files (originals and derivations).

        Versions must be organized later -- this is a flat listing.
        """
        sas = sas or self._get_session()
        filters = {} if filters is None else filters
        for entity in self._query(namespace, filters=filters, sas=sas):
            yield entity.to_dict(sas, versions=False)

    # Not currently used, except by the local storage
    def gen_keys(self, namespace, filters=None, sas=None):
        """Generator of the keys in a namespace."""
        sas = sas or self._get_session()
        q = self._query(
            namespace, filters=filters, what=self.file_model_cls.md5, sas=sas)
        for tup in q:
            yield tup[0]

    def get(self, namespace, key, sas=None):
        """Dict containing the metadata of one file, or None if not found."""
        sas = sas or self._get_session()
        entity = self._query(sas=sas, namespace=namespace, key=key).first()
        return entity.to_dict(sas) if entity else None

    def delete_with_versions(self, namespace, key, sas=None):
        """Delete a file along with all its versions."""
        sas = sas or self._get_session()
        original = self._query(
            sas=sas, namespace=namespace, key=key).one()
        for version in original.versions:
            sas.delete(version)
        sas.delete(original)

    def delete(self, namespace, key, sas=None):
        """Delete one file."""
        sas = sas or self._get_session()
        self._query(sas=sas, namespace=namespace, key=key).delete()


class BaseFile(ID, MinimalBase):
    """Base mixin class for a model that represents file metadata.

    The file MAY be an image.
    """

    # id = Primary key that exists because we inherit from ID
    md5 = Column(Unicode(32), nullable=False,
                 doc='hashlib.md5(file_content).hexdigest()')
    file_name = Column(
        Unicode(300),
        doc="Name of the original uploaded file, including extension")
    length = Column(Integer, nullable=False, doc='File size in bytes')
    created = now_column()  # Stores the moment the instance is created
    mime_type = Column(Unicode(255), doc='MIME type; e.g. "image/jpeg"')
    # http://stackoverflow.com/questions/643690/maximum-mimetype-length-when-storing-type-in-db
    image_width = Column(Integer, doc='Image width in pixels')
    image_height = Column(Integer, doc='Image height in pixels')
    version = Column(Unicode(20), default='original')

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

    def q_versions(self, sas, order_by='image_width'):
        """Query that returns files derived from this instance."""
        return sas.query(type(self)).filter_by(
            original_id=self.id).order_by(order_by)

    def __repr__(self):
        return '<{} #{} "{}" {}>'.format(
            type(self).__name__, self.id, self.file_name, self.version)

    def to_dict(self, sas, versions=True):
        """Convert this File, and optionally its versions, to a dictionary."""
        dic = super(BaseFile, self).to_dict()
        dic['versions'] = [v.to_dict(sas) for v in self.q_versions(sas)] \
            if versions else []
        return dic
