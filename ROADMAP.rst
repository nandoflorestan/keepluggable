=======
ROADMAP
=======


This version
============

- Validate settings with pydantic at startup and then store a
  separate configuration object within the orchestrator instance.
- File information, as converted to JSON, is too verbose! Find ways of
  making it smaller!
- Extract Payload (version) model from File model
  - File should contain: created, file_title, extension.
  - Payload should contain: image_height, image_width, length, md5, mime_type, extension, file_title, version_name (original would be ""), file_id, and href could be a property if the model can read configuration
- Fix inability to store .svg images
- Review CSRF protection


Urgent
======

- We should use classes (probably pydantic models) instead of dumb dictionaries
- Formalize action interface or use kerno actions
- Use reg or events instead of subclassing actions
- Add type annotations
- Add functional tests


Ideas
=====

- Integrate with Celery to create image versions in a background task
- Read EXIF data to fill in date and location, hopefully before the user types these
- Read other EXIF, IPTC, and XMP metadata in photo files
- Detect whether an image is already in the store and let the user edit it
- Allow the user to draw a square on the image to generate the thumbnail
- Configure what kinds of files are accepted (e. g. only images)
- generate image tag with alt, title (maybe legend) etc.
- trigger an event when image is uploaded
- search images to edit or remove them
- tags
- http caching
