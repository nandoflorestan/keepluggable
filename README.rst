===========
image_store
===========

Scope
=====

This is a highly configurable and pluggable system to manage storage of images and other documents (any kind of file, really), with metadata.

A user can upload images (or documents) and enter metadata about them, such as name, description, date, place, alt text, title attribute etc.

Some of the metadata shall be automatically found, such as image size, aspect ratio, geolocation data, MD5 checksum etc.

Multiple pluggable backends for payload storage are planned: Amazon S3, filesystem etc. You can add your own backend.

The metadata are stored separately from the payloads. Most people will use the provided SQLAlchemy metadata storage. Again, you can provide your own component for this.

The business rules are implemented in a separate layer (isolated from any of the storage strategies and any UI), called an "action" layer. (This is commonly known as a "service" layer, but we call it "action".)

One such action is the pluggable policy for uploaded image treatment. For instance, the default policy converts the original uploaded image to the JPEG format (so it will never store an unecessarily large BMP), with 1920px maximum for both width and height, then creates the following smaller versions of it as required:

- 960px (half size)
- 480px (quarter size)
- 240px (thumb size)

For those using the Pyramid web framework, some components are provided, too. There is an image_store resource that you can use with RESTful URLs such as these:

* my-img-store (GET, POST)
* my-img-store/1 (GET, PUT, DELETE)
* my-img-store/1?w=960&h=600 (GET)

Future
======

We want the experience to be as convenient as possible to the user:

* Detect whether an image is already in the store and let the user edit it
* Generate image slug from the name the user is typing
* Read EXIF data to fill in date and location, hopefully before the user types these
* Allow the user to draw a square on the image to generate the thumbnail
* Configure what kinds of files are accepted (e. g. only images)
* Define policies for formats: whether to convert/serve JPG, PNG, GIF
* generate image tag with alt, title (maybe legend) etc.
* trigger an event when image is uploaded
* search images to edit or remove them
* http caching
* tags

We are open to feature requests, suggestions and (especially) pull requests.
Reach us at
https://github.com/nandoflorestan/image_store
