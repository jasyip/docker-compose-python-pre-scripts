#!/bin/sh

: ${PYTHON_VERSIONS:="3.9 3.10 3.11"}

cd ..

for version in ${PYTHON_VERSIONS}; do
    podman build --build-arg "PYTHON_VERSION=${version}" -t "vps_python:${version}" . || exit
    podman run -t --rm \
            --user podman \
            --security-opt label=disable \
            --device /dev/fuse \
            "vps_python:${version}" || exit
done
