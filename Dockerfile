from quay.io/podman/stable

ARG PYTHON_VERSION=3.9

RUN dnf -y --best install "python${PYTHON_VERSION}" && \
    dnf clean all

# RUN echo podman:1000000:5000 > /etc/subuid && \
#     echo podman:1000000:5000 > /etc/subgid

RUN python${PYTHON_VERSION} -m ensurepip --upgrade
RUN pip${PYTHON_VERSION} install --upgrade --no-cache-dir pytest mypy


RUN ["podman", "pull", "hello-world"]

WORKDIR /home/podman

COPY --chown=podman:podman *.py ./
COPY --chown=podman:podman test_podman.sh ./

# RUN "python${PYTHON_VERSION}" functions.py

ENTRYPOINT mypy functions.py; pytest
