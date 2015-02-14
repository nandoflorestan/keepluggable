=================================
Getting started with keepluggable
=================================

::

	easy_install -UZ keepluggable

After installing the Python package, you can select the components you are using and then create a configuration file.


Selecting components
====================

File payload storage backends are available from keepluggable.storage_file.
File metadata storage backends are available from keepluggable.storage_metadata.


Understanding the configuration
===============================

In my case, I am integrating keepluggable with an existing Pyramid web app.
So I add a new ``[keepluggable]`` section to my Pyramid config file::

	[keepluggable]
	storage.file = keepluggable.storage_file.amazon_s3:AmazonS3Storage
	storage.metadata = keepluggable.storage_metadata.sql:SQLAlchemyMetadataStorage
	max_file_size = 23068672
	sql.file_model_cls = myapp.modules.uploads.models:File
	sql.session = myapp.database:session
	s3.access_key_id = SOME_KEY
	s3.secret_access_key = SOME_SECRET
	s3.region_name = SOME_REGION

Above you see a few [key, value] pairs. The section of an INI file
becomes a Python dictionary which is what the system actually uses as
configuration.

The first few settings define which components we are using. Each value is
comprised of a Python package name (containing dots), then a colon, then a
class name. What do they do?

- ``storage.file`` informs which backend class shall be used for file payload storage. In the example, we are using Amazon S3.
- ``storage.metadata`` informs which backend class shall be used for metadata storage. In the example, we are storing metadata with SQLAlchemy.

Each component we just selected needs its own configuration. Thus,
the Amazon S3 backend has settings beginning with "s3." and the
SQLAlchemy metadata storage has settings beginning with "sql.".

- ``sql.file_model_cls`` in the above example tells the SQLAlchemy backend to use a certain model class to store the file metadata.
- ``sql.session`` lets the SQLAlchemy backend know where to find the session.
- The settings beginning with "s3." provide information for the system to authenticate with Amazon.

This has been an overview of configuration. You should look up the
documentation for each component you are actually using in order to
see all the possible settings.


Integration with UI frameworks
==============================

Pyramid
-------

For those using the Pyramid web framework, a RESTful HTTP API is provided,
thin server style. Our AJAX views are based on URL traversal -- they are
attached to certain context resources -- so you can mount the resource
wherever you want in your URL scheme. For instance:

* /somewhere/down/the/url/my-img-store (GET, POST)
* /somewhere/down/the/url/my-img-store/1 (GET, PUT, DELETE)
* /somewhere/down/the/url/my-img-store/1?w=960&h=600 (GET)

`Read more about Pyramid integration. <http://github.com/nandoflorestan/keepluggable/blob/master/docs/integration_pyramid.rst>`_


Modifying a component for your use case
=======================================

Each component in the software has been factored to make it easy for you to
subclass it. When you implement your subclass, just change the configuration
so it points to your subclass rather than the original base class,
and you're done!
