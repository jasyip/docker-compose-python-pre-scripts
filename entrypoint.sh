#!/bin/sh

mypy functions.py

if [ "${PUDB_ON_ERROR}" = "1" ]; then
    PYTEST_ARGS="${PYTEST_ARGS:+${PYTEST_ARGS} }--pdbcls pudb.debugger:Debugger --pdb --capture=no"
    TERM=xterm-256color
fi

# shellcheck disable=SC2086
pytest ${PYTEST_ARGS}
