============
keepluggable
============

Scope
=====

**keepluggable** is an open source
`(MIT licensed) <http://github.com/nandoflorestan/keepluggable/blob/master/docs/LICENSE.rst>`_,
highly configurable Python library to manage storage of images and
other documents (any kind of file, really), with metadata.

The file metadata is stored in one place and the file payload in another.

For file payloads, we currently have implemented one backend that stores
them in Amazon S3. We also intend to provide another backend that stores
files in the local filesystem (mostly useful for usage during development).

For (optionally) storing the metadata we currently provide a SQLAlchemy
backend. In both cases, you can easily write other storage backends.

Using this library you can more easily have your user upload images
(or any kind of file) and enter metadata about them, such as name,
description, date, place, alt text, title attribute etc.

Some of the metadata is automatically found, such as file size, mime type,
image size, aspect ratio, geolocation data, MD5 checksum etc.

The code is highly decoupled so you can tweak the behaviour easily.

The business rules are implemented in a separate layer
(isolated from any of the storage strategies and any UI),
called an "action" layer. (This is commonly known as a "service" layer,
but we call it "action".) This makes it possible for us to have any
storage backends and use any web frameworks or other UI frameworks.

One such "action" is the pluggable policy for uploaded image treatment.
For instance, the default policy converts the original uploaded image
to the JPEG format (so it will never store an unecessarily large BMP),
optionally stores the original image in whatever size it is, then
creates configurable smaller versions of it:

- 1920px (HD)
- 960px (half size)
- 480px (quarter size)
- 240px (vignette)
- 160px (thumbnail)

`Get started! <http://github.com/nandoflorestan/keepluggable/blob/master/docs/getting-started.rst>`_


Future
======

We want the experience to be as convenient as possible for the user:

* Detect whether an image is already in the store and let the user edit it
* Generate image slug from the name the user is typing
* Optionally keep the original image stored (configurable)
* Read EXIF data to fill in date and location, hopefully before the user types these
* Allow the user to draw a square on the image to generate the thumbnail
* Configure what kinds of files are accepted (e. g. only images)
* Define policies for formats: whether to convert/serve JPG, PNG, GIF
* generate image tag with alt, title (maybe legend) etc.
* trigger an event when image is uploaded
* search images to edit or remove them
* http caching
* tags


Collaboration
=============

We want your help. We are open to bug reports, feature requests, suggestions
and (especially) pull requests. Reach us at
https://github.com/nandoflorestan/keepluggable
