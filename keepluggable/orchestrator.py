"""The *Orchestrator* coordinates the components you chose in configuration."""

from os import PathLike
from typing import Any, Dict, Iterable, Sequence, Union

from bag.reify import reify
from pydantic import PyObject, validator
import reg

from keepluggable import Pydantic, ReqStr


class Configuration(Pydantic):
    """Validated configuration of a keepluggable instance.

    ``settings`` should contain only the relevant section of an INI file.
    """

    name: ReqStr
    settings: Dict[str, Any]
    cls_storage_file: PyObject
    cls_storage_metadata: PyObject
    cls_action: PyObject

    @validator("cls_storage_file")
    def _validate_storage_file(cls, value):
        from .storage_file import BasePayloadStorage as BPS

        if not issubclass(value, BPS) or value is BPS:
            raise ValueError(
                "*cls_storage_file* must be a subclass of BasePayloadStorage."
            )
        return value


class Orchestrator:
    """A coordinator that instantiates configured components at startup.

    An Orchestrator instance provides:

    - ``storage_file``: the instance of the payload storage strategy class.
    - ``storage_metadata``: the instance of the metadata storage strategy.
    - ``get_action(namespace)``: conveniently get an instance of the
      action class, in order to serve a request.
    """

    instances: Dict[str, "Orchestrator"] = {}

    def __init__(self, config: Configuration) -> None:
        """Instantiate from a validated configuration object."""
        self.config = config
        self.storage_file = config.cls_storage_file(self)  # type: ignore
        self.storage_metadata = config.cls_storage_metadata(  # type: ignore
            self
        )
        Orchestrator.instances[config.name] = self
        self.action_config = config.cls_action.Config(  # type: ignore
            **config.settings
        )

    @classmethod
    def from_ini(
        cls, name: str, *paths: Union[str, PathLike], encoding: str = "utf-8",
    ) -> "Orchestrator":
        """Read one or more INI files and return an Orchestrator instance."""
        from configparser import ConfigParser

        parser = ConfigParser()
        parser.read(paths, encoding=encoding)
        section = parser["keepluggable " + name]
        config = Configuration(
            name=name,
            settings=section,
            cls_storage_file=section["cls_storage_file"],
            cls_storage_metadata=section["cls_storage_metadata"],
            cls_action=section["cls_action"],
        )
        return cls(config)

    def get_action(self, namespace: str) -> Any:
        """Conveniently instantiate the configured action class."""
        return self.config.cls_action(self, namespace)  # type: ignore

    def __repr__(self):
        return f'<Orchestrator "{self.config.name}">'


@reg.dispatch(  # Dispatch on the value of *name*.
    reg.match_key("name", lambda name, namespace: name)
)
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
