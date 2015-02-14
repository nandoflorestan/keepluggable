===================
Pyramid integration
===================

This documents describes how to integrate **keepluggable** with
your existing Pyramid application.


In the configuration phase
==========================

**keepluggable** needs to know the path to the current configuration .ini file.
This is because the keepluggable settings are put in a separate
``[keepluggable]`` section which it must read at startup.
So the Pyramid settings must contain a ``__file__`` variable whose value is
the ini file path. You can ensure this by adding the following to
the top of your app's WSGI function::

    def get_wsgi_app(global_settings, **settings):
        # global_settings contains the __file__, so make it available:
        for k, v in global_settings.items():
            settings.setdefault(k, v)

        # (...)
        # Then, after the Configurator is instantiated:
        config.include('keepluggable.web.pyramid')


Create a resource for the file storage
======================================

We use traversal and provide a context resource mixin class which you
must inherit in your own resource class::

    from keepluggable.web.pyramid.resources import BaseFilesResource


    class FilesResource(YourBaseResourceClass, BaseFilesResource):
        bucket_id = 42

The important thing is for this resource's instances to know which
bucket they should manage. It was done above through a static
class variable, but it need not be so static. It could be a Python property,
or an instance variable set by the constructor. Most of the time your code will
calculate the bucket ID based on the URL.

For instance, imagine your app has the URL "/collection/42/images".
If the resource corresponds to the "images" part of the URL,
maybe a "bucket_id" property would return "collection42".

More information is available on the
`BaseFilesResource docstring <http://github.com/nandoflorestan/keepluggable/blob/master/keepluggable/web/pyramid/resources.py>`_.
