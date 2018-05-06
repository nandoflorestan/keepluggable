"""keepluggable resources (for Pyramid traversal).

Usually an application will store its files in a single S3 bucket,
but there will be a need to namespace the files. This namespace
will depend on the parent resources in the URL. Thus, subclasses
must provide (as class variables or instance variables or properties):

- ``namespace``: A name for a namespace name that will contain files,
  such that a bucket will contain multiple namespaces.

Here is an example implementation that simply returns an integer::

    @reify
    def namespace(self):
        return self.__parent__.model_instance.id

You can have keepluggable integrated in your Pyramid application
multiple times, each time with different settings (expressed in a
different configuration section). For instance, you could have a
``[keepluggable avatars]`` INI section for users' images and also
a ``[keepluggable homes]`` INI section that would store a photo for
each address of these users. Each configuration section captures a
completely separate integration of keepluggable into your app.

Therefore, subclasses of this resource must provide:

- ``keepluggable_name``: The suffix of the INI section (the part
  after "keepluggable ").

Resources must also provide ``__name__`` and ``__parent__``. You can
read more about this in the Pyramid docs.
"""

from keepluggable.orchestrator import Orchestrator
from pyramid.decorator import reify


class BaseResource:

    @reify
    def orchestrator(self) -> Orchestrator:
        """Return the Orchestrator instance relevant to this resource."""
        return Orchestrator.instances[self.keepluggable_name]  # type: ignore

    @reify
    def action(self):
        return self.orchestrator.get_action(self.namespace)


class BaseFilesResource(BaseResource):
    """Base for a Pyramid traversal resource representing a file store."""


class BaseFileResource(BaseResource):
    """Pyramid traversal resource representing a specific file.

    Here is an example resource using this as a base class::

        class FileResource(BaseFileResource):
            # This resource is governed by INI section "[keepluggable_file]":
            keepluggable_name = "file"

            @reify
            def namespace(self):
                return parent(self).id
    """
