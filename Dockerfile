from quay.io/podman/stable

ARG PYTHON_VERSION=3.9

RUN dnf -y --best install "python${PYTHON_VERSION}" && \
    dnf clean all

# RUN echo podman:1000000:5000 > /etc/subuid && \
#     echo podman:1000000:5000 > /etc/subgid

RUN python${PYTHON_VERSION} -m ensurepip --upgrade
RUN pip${PYTHON_VERSION} install --upgrade --no-cache-dir pytest mypy pudb


RUN ["podman", "pull", "hello-world"]

USER podman
WORKDIR /home/podman

ENV PYTEST_ARGS=
ENV PUDB_ON_ERROR=0

COPY --chown=podman functions.py ./
COPY --chown=podman tests ./tests
COPY --chown=podman entrypoint.sh ./
COPY --chown=podman .pudb.cfg ./.config/pudb/pudb.cfg

ENTRYPOINT ["sh", "entrypoint.sh"]
