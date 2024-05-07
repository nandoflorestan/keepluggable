"""The *Orchestrator* coordinates the components you chose in configuration."""

from __future__ import annotations  # allows forward references; python 3.7+
from configparser import SectionProxy
from os import PathLike
from typing import Any, Union

from bag.text import strip_preparer
import colander as c
from kerno.typing import DictStr
import reg


class ConfigurationSchema(c.Schema):
    """Validated configuration of a keepluggable instance.

    ``settings`` should contain only the relevant section of an INI file.
    """

    @staticmethod
    def _validate_storage_file(node, value):
        from .storage_file import BasePayloadStorage as BPS

        if not issubclass(value, BPS) or value is BPS:
            raise c.Invalid(
                node, "*cls_storage_file* must be a subclass of BasePayloadStorage."
            )

    name = c.SchemaNode(c.Str(), preparer=strip_preparer, validator=c.Length(min=1))
    cls_action = c.SchemaNode(c.GlobalObject(package=None))
    cls_storage_metadata = c.SchemaNode(c.GlobalObject(package=None))
    cls_storage_file = c.SchemaNode(
        c.GlobalObject(package=None),
        validator=_validate_storage_file.__func__,  # type: ignore[attr-defined]
    )


class Orchestrator:
    """A coordinator that instantiates configured components at startup.

    An Orchestrator instance provides:

    - ``storage_file``: the instance of the payload storage strategy class.
    - ``storage_metadata``: the instance of the metadata storage strategy.
    - ``get_action(namespace)``: conveniently get an instance of the
      action class, in order to serve a request.
    """

    instances: dict[str, "Orchestrator"] = {}

    def __init__(self, config: DictStr) -> None:
        """Instantiate from a validated configuration dictionary."""
        name = config["name"]
        assert None is Orchestrator.instances.get(
            name
        ), f"Orchestrator instantiated more than once: {name}"
        self.config = config
        self.storage_file = config["cls_storage_file"](self)
        self.storage_metadata = config["cls_storage_metadata"](self)
        Orchestrator.instances[name] = self
        self.action_config: DictStr = config["cls_action"].get_config(
            config["settings"]
        )

    @classmethod
    def instantiate_validating(
        cls, name: str, section: DictStr | SectionProxy
    ) -> Orchestrator:
        """Validate the configuration section and return the Orchestrator."""
        config: DictStr = ConfigurationSchema().deserialize(
            {
                "name": name,
                "cls_storage_file": section["cls_storage_file"],
                "cls_storage_metadata": section["cls_storage_metadata"],
                "cls_action": section["cls_action"],
            }
        )
        config["settings"] = section  # each component takes its own settings from here
        return cls(config)

    @classmethod
    def from_ini(
        cls,
        name: str,
        *paths: Union[str, PathLike],
        encoding: str = "utf-8",
    ) -> Orchestrator:
        """Read one or more INI files and return an Orchestrator instance."""
        from configparser import ConfigParser

        parser = ConfigParser()
        parser.read(paths, encoding=encoding)
        section = parser["keepluggable " + name]
        return cls.instantiate_validating(name=name, section=section)

    def get_action(self, namespace: str) -> Any:
        """Conveniently instantiate the configured action class."""
        return self.config["cls_action"](self, namespace)

    def __repr__(self) -> str:
        return f'<Orchestrator "{self.config["name"]}">'


@reg.dispatch(  # Dispatch on the value of *name*.
    reg.match_key("name", lambda name, namespace: name)
)
def get_middle_path(name: str, namespace: Any) -> str:
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
