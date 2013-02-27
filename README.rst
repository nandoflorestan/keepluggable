image_store
===========

Scope
=====

This is a pluggable Pyramid app that manages image storage with metadata.

A user can upload images and enter metadata about them, such as name, description, date, place etc.

The application stores the image using one of several strategies and then it
can serve the image in any size. The size is specified in the URL and a version of the image is created dynamically. There is a cache, too, so maybe the image already exists and is directly served.

The app uses URLs such as these:

* my-img-store
* my-img-store/@@add
* my-img-store/1/@@edit
* my-img-store/1/@@delete
* my-img-store/1?w=960&h=600
* my-img-store/1/@@thumb/40x30

Future
======

We want the experience to be as convenient as possible to the user:

* Detect whether an image is already in the store and let the user edit it
* Generate image slug from the name the user is typing
* Read EXIF data to fill in date and location, hopefully before the user types these
* Create a thumbnail automatically, then let the user change it
* The thumbnail also can be served in any size.
* LRU cache for image sizes
* Don't store BMP images; convert them first
* define policies for formats: whether to convert/serve JPG, PNG, GIF
* generate image tag with alt, title (maybe legend) etc.
* trigger an event when image is uploaded
* search images to edit or remove them
* http caching
* tags

We are open to feature requests, suggestions and (especially) pull requests.
Reach us at
https://github.com/nandoflorestan/image_store
