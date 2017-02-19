=======
ROADMAP
=======


This version
============

- Fix inability to store .svg images
- Use / instead of - to separate the namespace in the filename
- Review CSRF protection


Urgent
======

- Add functional tests
- Maybe use reg instead of subclassing actions?


Ideas
=====

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
