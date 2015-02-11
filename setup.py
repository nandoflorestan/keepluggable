#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Installer for keepluggable'''

import os
from setuptools import setup, find_packages
# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide
from codecs import open

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

# CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['nine', 'bag']

setup(name='keepluggable',
    version='0.1dev1',
    description='Manages storage of images and other documents, with metadata.'
    ' Also offers a Pyramid UI',
    long_description=long_description,
    classifiers=[  # http://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 3 - Alpha',
        # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        'Programming Language :: Python :: Implementation :: CPython',
        "Framework :: Pyramid",
        'Topic :: Database',
        "Topic :: Internet :: WWW/HTTP",
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    author='Nando Florestan',
    author_email="nandoflorestan@gmail.com",
    url='https://github.com/nandoflorestan/keepluggable',
    keywords='web pylons pyramid images store thumbnails',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    # tests_require=requires,
    # test_suite="keepluggable",
    entry_points="""\
    [paste.app_factory]
    main = keepluggable:main
    """,
    )
