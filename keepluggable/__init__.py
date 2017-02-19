"""**keepluggable** contains reusable code that stores files and images."""

from bag.settings import resolve  # TODO Replace
REQUIRED = object()

# TODO Move to bag


def SettingsFromFiles(*paths, encoding='utf-8'):
    """Read one or more INI files and return a single Settings instance."""
    from configparser import ConfigParser
    parser = ConfigParser()
    parser.read(paths, encoding=encoding)
    return Settings(parser)


class Settings(object):
    """Convenient API for reading settings."""

    REQUIRED = object()

    def __init__(self, adict):
        """Create an instance from a dict-like object."""
        if not hasattr(adict, 'get') or not hasattr(adict, '__getitem__'):
            raise TypeError("The *adict* argument must be dict-like. "
                            "Received: {}".format(adict))
        self.adict = adict

    def read(self, key, section=None, default=REQUIRED):
        """Merely return the value associated with ``key``."""
        adict = self.adict if section is None else self.adict[section]
        if default is self.REQUIRED:
            try:
                return adict[key]
            except KeyError:
                raise RuntimeError(
                    'Settings do not contain a "{}" key in its "{}" section.'
                    .format(key, section or 'default'))
        else:
            return adict.get(key, default)

    def resolve(self, key, section=None, default=REQUIRED):
        """For values that point to Python objects, return the object."""
        resource_spec = self.read(key, section, default)
        return None if resource_spec is None else resolve(resource_spec)
