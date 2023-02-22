#!/bin/sh

: ${PYTHON_VERSIONS:="3.9 3.10 3.11"}

for version in ${PYTHON_VERSIONS}; do
    podman build --build-arg "PYTHON_VERSION=${version}" -t "vps_python:${version}" . || exit
done
