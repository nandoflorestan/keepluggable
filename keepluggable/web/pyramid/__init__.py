"""Integration with the Pyramid web framework.

Usage is described in the "Pyramid integration" page of the documentation.
"""

from keepluggable import Settings
from keepluggable.orchestrator import IOrchestrator, Orchestrator

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory('keepluggable')
del TranslationStringFactory


def add_keepluggable(config, dict_or_path, storage_name, encoding='utf-8'):
    """Add a keepluggable storage to this web app.

    ``dict_or_path`` must be either a dictionary-like object containing the
    configuration settings for this keepluggable storage, or the path to an
    INI file containing those settings.

    ``storage_name`` must be a string, a unique ID for this storage in the app.
    """
    _register_orchestrator(
        config.registry,
        _make_keepluggable(dict_or_path, storage_name, encoding=encoding),
    )


def _make_keepluggable(dict_or_path, storage_name, encoding='utf-8'):
    if isinstance(dict_or_path, str):
        ini_path = dict_or_path
        from configparser import ConfigParser
        parser = ConfigParser()
        parser.read(ini_path, encoding=encoding)
        config_section_name = 'keepluggable ' + storage_name
        adict = parser[config_section_name]
    elif hasattr(dict_or_path, '__getitem__'):
        adict = dict_or_path
    else:
        raise RuntimeError('The argument dict_or_path may not be {}'.format(
            type(dict_or_path).__name__))
    return Orchestrator(storage_name, Settings(adict))


def _register_orchestrator(registry, orchestrator):
    registry.registerUtility(
        component=orchestrator,
        provided=IOrchestrator,
        name=orchestrator.name)


def get_orchestrators(registry):
    """Return a generator of 2-tuples: ``(name, orchestrator)``."""
    return registry.getUtilitiesFor(IOrchestrator)


def get_orchestrator(context, request):
    """Return the orchestrator that is relevant to the current request.

    The first parameter, ``context``, can be the request context or the
    keepluggable storage name.
    """
    return request.registry.getUtility(
        IOrchestrator,
        context if isinstance(context, str)
        else context.keepluggable_name)


def includeme(config):
    """Pyramid integration. Add a configurator directive to be used next."""
    config.add_directive('add_keepluggable', add_keepluggable)
