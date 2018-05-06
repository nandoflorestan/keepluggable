"""Integration with the Pyramid web framework.

Usage is described in the "Pyramid integration" page of the documentation.
"""

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory('keepluggable')
del TranslationStringFactory
