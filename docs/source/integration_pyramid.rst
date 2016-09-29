===================
Pyramid integration
===================

This page describes how to integrate **keepluggable** into
your existing Pyramid application by reusing the code in the
:py:mod:`keepluggable.web.pyramid` package.

Of course you can always write your own Pyramid integration reusing our code.


Configuration
=============

**keepluggable** is a pluggable sub-application that can be integrated into
your app **multiple times**. Each time you start by creating a section in
your INI file. Section names must start with "keepluggable ".
In the following example 2 keepluggable storages are configured::

    [app:main]
    # Pyramid application settings go in this section.
    # (...)

    [keepluggable avatars]
    # User images storage settings here
    # (...)

    [keepluggable products]
    # The storage for product images is configured in this section.
    # (...)


At application startup
======================

Start by including **keepluggable** after Pyramid's Configurator
is instantiated::

    config.include('keepluggable.web.pyramid')

This does almost nothing: it only makes a new config method available.
You have to use it next::

    config.add_keepluggable(  # Directive that adds a keepluggable storage
        global_settings['__file__'],  # Path to your INI configuration file
        'avatars',                    # A unique name for this storage.
        )

This will cause **keepluggable** to read the "[keepluggable avatars]"
section you created earlier and set it up.

Repeat the call for each separate storage::

    config.add_keepluggable(  # Directive that adds a keepluggable storage
        global_settings['__file__'],  # Path to your INI configuration file
        'products',                   # A unique name for this storage.
        )

The first argument can be a settings dictionary, too -- but we recommend
you set things up with INI sections as described above.


Create a resource for the file storage
======================================

We use traversal and provide a context resource mixin class which you
must inherit in your own resource class::

    from keepluggable.web.pyramid.resources import BaseFilesResource


    class FilesResource(YourBaseResourceClass, BaseFilesResource):
        keepluggable_name = "avatars"  # name of the storage for this resource
        namespace = 'myapp42'

The ``keepluggable_name`` variable above lets the resource determine which
of the keepluggable storages is "mounted" on this URL.

You can use the ``namespace`` setting to further separate files. So this
resource knows which namespace it manages. It was done above through a static
class variable, but it need not be so static. It could be a Python property,
or an instance variable set by the constructor. Your code might
calculate the namespace based on the URL.

More information is available on the component documentation:
:py:mod:`keepluggable.web.pyramid.resources`


We provide a RESTful HTTP API done with Pyramid
===============================================

Once you have a resource, you can attach views to it. See
:py:mod:`keepluggable.web.pyramid.views`.

Below we provide a description of what the HTTP API does.


List existing files and images
------------------------------

**GET example URL: /users/joe/files**

The JSON-encoded response contains, in its "items" variable, an array of
metadata objects about the *original* uploaded files. Each metadata contains
data such as id, md5, length, image_height, image_width, image_format,
file_name, version etc.

For each metadata, if versions of the original were created
(e. g. smaller images), they are inside the "versions" variable.
They contain an "href" variable indicating the payload location.


Upload one or more files or images
----------------------------------

**POST example URL: /users/joe/files**

Other requests in this API must be in JSON format. Not this method!
It must be a common multipart/form-data POST request.

It must contain the upload(s) in a ``files`` variable. You may also specify
other variables -- they are forwarded to your metadata storage backend.

Most of the metadata is discovered on the server. This includes
file length, file name, MD5 hash, image format, image size etc.

The response is in JSON format (only the request isn't) and it has
**items**, an array in which each element is either
the metadata for an accepted file, or details of upload failure.
You can test failures by uploading zero-length files.
The order in the ``items`` array is the same as the uploaded *files*.

Each failure has these variables:

- ``"upload_failed": true``: A flag for you to identify the failures
- ``error_type``: An error title, such as '"MY_FILE" was not stored. '
- ``error_msg``: A message that should be displayed to the user
- ``file_name``: The uploaded file name
- ``mime_type``: The MIME type reported by the browser


Updating the metadata of a file or image
----------------------------------------

**PUT example URL: /users/joe/files/<id>/@@metadata**

In this case, the file is NOT identified by its MD5, but by its ID.
There are 2 modes of operation:

- If you do not implement and indicate a Colander schema, every variable
  in the request is set on the metadata entity.
- If you do implement and indicate a Colander schema, it gets used for
  validation and the metadata entity only receives the "cleaned" data.

The most important variable that is set through this method is the
**description**, since it is usually not sent with the original upload
request.


Delete/remove a file
--------------------

**DELETE example URL: /users/joe/files/<MD5>**

That last bit in the URL must be the MD5 hash (also known as the "key")
of the file that should be deleted.

This method deletes all the derivative files as well ("versions").
It deletes payloads as well as metadata entities.

No request body is necessary. May return *404 Not Found* if the resource
does not exist. When happy, returns *204 No Content*, meaning the resource
was deleted and the response has no body.
