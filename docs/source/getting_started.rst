===============
Getting started
===============

::

    easy_install -UZ keepluggable

After installing the Python package, you can select the components
you are using and then create a configuration file.  Each component you
decide to use has its own settings, so you must read the respective
documentation section.


Selecting components
====================

**File payload storage backends:**

- :py:class:`keepluggable.storage_file.amazon_s3.AmazonS3Storage`
  is recommended for production.
- :py:class:`keepluggable.storage_file.local.LocalFilesystemStorage`
  is a storage backend using the local file system. It is too simple,
  useful during development.
- You can write a new payload storage backend. I hear Rackspace also has a
  nice file storage solution...

**File metadata storage backends:**

- :py:class:`keepluggable.storage_metadata.sql.SQLAlchemyMetadataStorage`
- You can write a new metadata storage backend. ZODB, Mongo, gdbm, anyone?

**Action (workflow) backends:**

- :py:class:`keepluggable.actions.BaseFilesAction`
  is the basic action that fills in basic metadata such as MD5, file name, file size etc. and stores the file in the aforementioned backends.
- :py:class:`keepluggable.image_actions.ImageAction`
  is a workflow class that does everything that BaseFilesAction does, but has
  additional features for image files.


Understanding configuration
===========================

In my case, I am integrating keepluggable with an existing Pyramid web app
so it will store users' docs. So I add a new ``[keepluggable docs]``
section to my Pyramid config file::

    [keepluggable docs]
    # The components we chose:
    storage.file = keepluggable.storage_file.amazon_s3:AmazonS3Storage
    storage.metadata = keepluggable.storage_metadata.sql:SQLAlchemyMetadataStorage
    action.files = keepluggable.actions:BaseFilesAction

    # AmazonS3Storage configuration:
    s3.access_key_id = SOME_KEY
    s3.secret_access_key = SOME_SECRET
    s3.region_name = SOME_REGION
    s3.bucket = BUCKET_NAME

    # SQLAlchemyMetadataStorage configuration:
    sql.file_model_cls = myapp.modules.docs.models:File
    sql.session = myapp.database:session

    # action.files configuration keys have a "fls." prefix:
    fls.max_file_size = 23068672

Above you see a few ``[key = value]`` pairs. At startup this INI file section
is read into a Python dictionary which is what the system actually uses as
configuration.

The first group of settings define which components we are using.
Each value is comprised of a Python package name (containing dots),
then a colon, then a class name. What do they do?

- ``storage.file`` informs which backend class shall be used for
  file payload storage. In the example, we are using Amazon S3.
- ``storage.metadata`` informs which backend class shall be used for
  metadata storage. In the example, we are storing metadata with SQLAlchemy.
- ``action.files`` points to an "Action" class that contains the actual steps
  that will be carried out in the workflow. Thus, probably this will point
  to your own subclass instead of the value given in the example.

Each component we just selected needs its own configuration. Thus,
the Amazon S3 backend has settings beginning with "s3." and the
SQLAlchemy metadata storage has settings beginning with "sql.".

To configure each component you selected, please refer to that component's
own documentation -- it should mention all the possible settings.


Integration with UI frameworks
==============================

Pyramid
-------

For those using the Pyramid web framework, a RESTful HTTP API is provided,
thin server style. Our AJAX views are based on URL traversal -- they are
attached to certain context resources -- so you can mount the resource
wherever you want in your URL scheme. For instance:

- /somewhere/down/the/url/my-img-store (GET, POST)
- /somewhere/down/the/url/my-img-store/1 (GET, PUT, DELETE)
- /somewhere/down/the/url/my-img-store/1?w=960&h=600 (GET)

:doc:`Read more about Pyramid integration<integration_pyramid>`.


Modifying a component for your use case
=======================================

Each component in the software has been factored to make it easy for you to
subclass it. When you implement your subclass, just change the configuration
so it points to your subclass rather than the original base class,
and you're done!


Concepts for developers
=======================

Whenever I speak of file **metadata**, I mean an entity that looks like this::

    {
     "id": 7,
     "md5": "8b99d5f9c79bee5f300f35432477a853",
     "created": "2015-02-26T18:54:23.541624",
     "description": "",
     "file_name": "20140913_153756.jpg",
     "href": "http://some.address.com/path/to/the/image.jpg",
     "image_format": "JPEG",
     "image_width": 3264,
     "image_height": 2448,
     "length": 3803890,
     "mime_type": "image/jpeg",
     "original_id": null,
     "version": "original",
     "versions": [],
    }

The "id" and "md5" variables both serve as file identifiers.
"length" contains the file size in bytes.
When the file is not an image, the variables that start with "image\_" are null.

The file always belongs to a namespace which is usually expressed in the URL,
not in the metadata entity.

The file may be an original (something a user uploaded) or a version of it
(such as a thumbnail). The version name is found in the "version" variable.
Uploaded files have ``version == "original"``. Original files contain their
versions in the "versions" array. Derivative files have their "versions"
array empty, but they mention the "original_id".
