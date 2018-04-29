"""The *Orchestrator* coordinates the components you chose in configuration."""

from bag.reify import reify
import reg
from zope.interface import Interface, implementer, Attribute
from .storage_file import BasePayloadStorage


class IOrchestrator(Interface):
    """Represents the materialization of the components chosen in settings."""

    storage_file = Attribute('payload storage strategy instance')
    storage_metadata = Attribute('metadata storage strategy instance')
    action_cls = Attribute('action strategy class')


@implementer(IOrchestrator)
class Orchestrator:
    """The coordinator of your configured components.

    An Orchestrator instance provides as its variables:

    - ``storage_file``: the instance of the payload storage strategy class.
    - ``storage_metadata``: the instance of the metadata storage strategy.
    - ``action_cls``: the configured action class, ready to be instantiated.
    """

    def __init__(self, name, settings):
        """``settings`` contains only the relevant section of the INI file."""
        self.name, self.settings = name, settings
        self._instantiate_payload_storage()
        self._instantiate_metadata_storage()
        self.action_configuration = self._validate_action_configuration()

    def _instantiate_payload_storage(self):
        storage_cls = self.settings.resolve('storage.file')
        assert issubclass(storage_cls, BasePayloadStorage)
        self.storage_file = storage_cls(self)

    def _instantiate_metadata_storage(self):
        storage_cls = self.settings.resolve('storage.metadata')
        self.storage_metadata = storage_cls(self)

    @reify
    def action_cls(self):
        """Return the *action* class configured for this storage."""
        return self.settings.resolve('action.files')

    def _validate_action_configuration(self):
        """Validate settings for the action class against the schema."""
        # Select settings that start with a prefix like "fls."
        prefix = self.action_cls.SETTINGS_PREFIX
        raw_settings = {
            key[len(prefix):]: val
            for key, val in self.settings.adict.items()
            if key.startswith(prefix)}
        schema = self.action_cls.ConfigurationSchema()
        return schema.deserialize(raw_settings)

    def get_action(self, namespace):
        """Conveniently instantiate the configured action class."""
        return self.action_cls(self, namespace)


@reg.dispatch(  # Dispatch on the value of *name*.
    reg.match_key('name', lambda name, namespace: name))
# Cannot type-annotate this function, Reg 0.11 does not support it
def get_middle_path(name, namespace):
    """Return the path between bucket and file name.

    By default this simply returns the ``namespace``. This means the
    default naming scheme is: ``bucket / namespace / file_name``

    BUT you can override this function for each keepluggable instance
    in your application.

    By creating multiple naming schemes, you can have multiple storages
    living in the same bucket without clashing!

    We use the Reg library to accomplish this. It implements dispatch
    based on function arguments. This particular function will dispatch
    based on the value of the ``name`` argument, which should be
    the same as the name of a keepluggable instance.

    For instance, your keepluggable instance that stores user avatars
    could register one implementation such as::

        return "avatar{}".format(namespace)

    ...and then a different area of your app could have a keepluggable instance
    that stores company logos by registering another implementation::

        return "logo{}".format(namespace)

    ...and so these can share a single S3 bucket.
    """
    return str(namespace)
