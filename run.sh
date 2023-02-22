#!/bin/sh

: ${PYTHON_VERSIONS:="3.9 3.10 3.11"}

for version in ${PYTHON_VERSIONS}; do
    podman run -t --rm \
            --user podman \
            --security-opt label=disable \
            --device /dev/fuse \
            "vps_python:${version}"
done


        # --entrypoint '/home/podman/test_podman.sh' \
