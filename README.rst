============
keepluggable
============

Scope
=====

**keepluggable** is an open source,
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

`Get started with keepluggable! <http://docs.nando.audio/keepluggable/latest/getting-started.html>`_


Future
======

We want the experience to be as convenient as possible for the user:

- CSRF protection
- Read EXIF data to fill in date and location, hopefully before the user types these
- Read other EXIF, IPTC, and XMP metadata in photo files
- Detect whether an image is already in the store and let the user edit it
- Allow the user to draw a square on the image to generate the thumbnail
- Configure what kinds of files are accepted (e. g. only images)
- generate image tag with alt, title (maybe legend) etc.
- trigger an event when image is uploaded
- search images to edit or remove them
- http caching
- tags
- Integrate with Celery to create image versions in a background task


Collaboration
=============

We want your help. We are open to bug reports, feature requests, suggestions
and (especially) pull requests. Reach us at
https://github.com/nandoflorestan/keepluggable/issues
