from quay.io/podman/stable

RUN dnf -y --best install python3 python3-pytest python3-mypy && \
    dnf clean all

RUN echo podman:1000000:5000 > /etc/subuid && \
    echo podman:1000000:5000 > /etc/subgid


RUN ["podman", "pull", "hello-world"]

WORKDIR /home/podman

COPY --chown=podman:podman *.py ./
COPY --chown=podman:podman test_podman.sh ./

ENTRYPOINT mypy functions.py; pytest
