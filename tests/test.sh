#!/bin/sh


SCRIPT_DIR="$(dirname "$(readlink -f "${0}")")"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
cd "${ROOT_DIR}"

if [ -f .env ]; then
    set -o allexport
    source ./.env
    set +o allexport
fi

: ${CONTAINER_EXECUTABLE:=/usr/bin/docker}
: ${PUDB_CONF_DIR:=${XDG_CONFIG_HOME}/pudb}
CONTAINER_RUN_FLAGS="-it --rm --env-file .env --user podman --security-opt label=disable --device=/dev/fuse"

for version in ${PYTHON_VERSIONS}; do
    "${CONTAINER_EXECUTABLE}" build \
            --build-arg "PYTHON_VERSION=${version}" \
            -t "${TEST_CONTAINER_NAME}:${version}" \
            . \
            || exit

    if [ "${PUDB_ON_ERROR}" -eq 1 ] && [ -d "${PUDB_CONF_DIR}" ]; then
        CONTAINER_RUN_FLAGS="${CONTAINER_RUN_FLAGS:+${CONTAINER_RUN_FLAGS} } --mount type=bind,src=${PUDB_CONF_DIR},dst=${XDG_CONFIG_HOME}/pudb,ro"
    fi

    "${CONTAINER_EXECUTABLE}" run ${CONTAINER_RUN_FLAGS} "vps_python:${version}" || exit
done
