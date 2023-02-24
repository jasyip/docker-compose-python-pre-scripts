#!/bin/sh

: ${PYTHON_VERSIONS:="3.9 3.10 3.11"}

SCRIPT_DIR="$(dirname "$(readlink -f "${0}")")"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
cd "${ROOT_DIR}"

for version in ${PYTHON_VERSIONS}; do
    podman build --build-arg "PYTHON_VERSION=${version}" -t "vps_python:${version}" . || exit
    podman run -t --rm \
            --user podman \
            --security-opt label=disable \
            --device /dev/fuse \
            "vps_python:${version}" || exit
done
