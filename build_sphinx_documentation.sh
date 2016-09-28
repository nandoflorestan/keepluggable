#! /bin/sh

PACKAGE=../keepluggable
API=source/api

cd docs && \
rm -r $API

# Generate the API docs automatically
sphinx-apidoc -H "keepluggable API" --separate -o $API $PACKAGE && \
make html && \
cd - > /dev/null && \
echo "To read the local docs, type:  xdg-open docs/build/html/index.html"
