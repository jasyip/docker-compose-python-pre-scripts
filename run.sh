#!/bin/sh

podman run -t --rm \
        --user podman \
        --security-opt label=disable \
        --device /dev/fuse \
        vps_python

        # --entrypoint '/home/podman/test_podman.sh' \
