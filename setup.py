#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Installer for keepluggable"""

from codecs import open
from sys import version_info
from setuptools import setup, find_packages
# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

requires = [  # Each backend may have additional dependencies.
    'nine', 'bag>=1.0.0',
    ]

if version_info[:2] < (3, 4):
    requires.append('pathlib')  # 'enum34'
# if version_info[:2] < (3, 2):
#     requires.extend(['futures', 'unittest2'])

setup(
    name='keepluggable',
    version='0.3.2',
    description='Manages storage of images and other files, with metadata.'
    ' Also offers an HTTP API done on Pyramid.',
    long_description=long_description,
    classifiers=[  # http://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 4 - Beta',
        # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
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
    # entry_points="""\
    # [paste.app_factory]
    # main = keepluggable:main
    # """,
    )
