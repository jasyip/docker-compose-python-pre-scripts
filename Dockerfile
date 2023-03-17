from quay.io/podman/stable


ARG PYTHON_PACKAGE

RUN dnf -y --best install "${PYTHON_PACKAGE}" && \
    dnf clean all

# RUN echo podman:1000000:5000 > /etc/subuid && \
#     echo podman:1000000:5000 > /etc/subgid

RUN ${PYTHON_PACKAGE} -m ensurepip
RUN ${PYTHON_PACKAGE} -m pip install --upgrade --no-cache-dir pip pytest mypy pudb


RUN ["podman", "pull", "hello-world"]

USER podman
WORKDIR /home/podman

ENV PYTEST_ARGS=
ENV PUDB_ON_ERROR=0

COPY --chown=podman .pudb.cfg ./.config/pudb/pudb.cfg
COPY --chown=podman entrypoint.sh ./
COPY --chown=podman functions.py ./
COPY --chown=podman tests ./tests

ENTRYPOINT ["sh", "entrypoint.sh"]
