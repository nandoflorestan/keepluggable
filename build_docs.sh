#! /bin/sh

PACKAGE=../keepluggable
API=source/api

cd docs

# Generate the API docs automatically
rm -r $API
sphinx-apidoc -H "keepluggable API" -o $API $PACKAGE

# Generate the rest based on index.rst
make html

cd -
