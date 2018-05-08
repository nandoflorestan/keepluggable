=======================================
keepluggable, the reusable file storage
=======================================


Scope
=====

`keepluggable <https://pypi.python.org/pypi/keepluggable>`_ is an open source,
`(MIT licensed) <http://docs.nando.audio/keepluggable/latest/LICENSE.html>`_,
highly configurable Python library to **manage storage of images and
other documents** (any kind of file, really), with metadata.

The documentation is at http://docs.nando.audio/keepluggable/latest/

The file **metadata** can be stored in a different place than the file payload.
This is recommended because many operations, such as listing files,
do not involve actual file content, so you should avoid loading it.
Also, payloads should be optimized for serving and metadata should be
optimized for querying.

For file payloads, we currently have implemented one backend that stores
them in Amazon S3. There is also a very simple backend that stores
files in the local filesystem (useful during development).

For (optionally) storing the metadata we currently provide a base SQLAlchemy
backend for you to subclass.

In both cases, you can easily write other storage backends.

Using this library you can more easily have your user upload images
(or any kind of file) and enter metadata about them, such as name,
description, date, place, alt text, title attribute etc.

Some of the metadata is automatically found, such as file size, mime type,
image size, aspect ratio, MD5 checksum etc.

The code is highly decoupled so you can tweak the behaviour easily.

The business rules are implemented in a separate layer
(isolated from any of the storage strategies and any UI),
called an "action" layer. (This is commonly known as a "service" layer,
but we call it "action".) This makes it possible for us to have any
storage backends and use any web frameworks or other UI frameworks.

Each application has its own business rules, therefore it is likely that
you will subclass the provided action layer to tweak the workflow for
your purposes.

One such "action" is the pluggable policy for uploaded image treatment.
For instance, the default policy converts the original uploaded image
to the JPEG format (so it will never store an unecessarily large BMP),
optionally stores the original image in whatever size it is, then
creates configurable smaller versions of it.

Some cameras do not rotate the photo, they just add orientation metadata to the
image file, so keepluggable rotates it for you, before creating the thumbnails.

`Get started with keepluggable! <http://docs.nando.audio/keepluggable/latest/getting_started.html>`_


Collaboration
=============

We want your help. We are open to feature requests, suggestions,
`bug reports <https://github.com/nandoflorestan/keepluggable/issues>`_
and
`pull requests <https://github.com/nandoflorestan/keepluggable>`_,
in reverse order of openness.


Migration to keepluggable 0.8
=============================

keepluggable 0.8 changes the way files are stored. How?

- It separates namespaces using the "/" character rather than "-". This
  creates a better user experience in the S3 Management console.
- Now you can use only one bucket per environment if you wish to.
  Multiple keepluggable integrations (in a single app) can use the
  same bucket, because each keepluggable integration can use its
  own directories.
- Between the bucket name and the file name you can create your own
  directory scheme (e. g. "/users/42/avatars/angry_mode/"). I am calling
  this a "middle path". See the function ``get_middle_path()`` in the
  *orchestrator.py* file.

A migration function is provided so you can update your old storages
to keepluggable 0.8. See the method ``migrate_bucket()`` in the file
*amazon_s3.py*.

The names of the configuration settings also changed in 0.8.
