#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Installer for image_store'''

import os
from setuptools import setup, find_packages
# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
# CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    # 'transaction',
    # 'pyramid_tm',
    # 'pyramid_debugtoolbar',
    'six',
    'waitress',
    ]

setup(name='image_store',
    version='0.1dev',
    description='Pluggable Pyramid app: upload images, metadata, '
    'serve thumbnails',
    long_description=README,
    classifiers=[ # TODO add more
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
    author='Nando Florestan',
    author_email="nandoflorestan@gmail.com",
    url='https://github.com/nandoflorestan/image_store',
    keywords='web pylons pyramid images store thumbnails',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    test_suite="image_store",
    entry_points="""\
    [paste.app_factory]
    main = image_store:main
    """,
    )
