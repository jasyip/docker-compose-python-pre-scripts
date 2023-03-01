#!/bin/sh

mypy functions.py

if [ "${PUDB_ON_ERROR}" = "1" ]; then
    PYTEST_ARGS="${PYTEST_ARGS:+${PYTEST_ARGS} }--pdbcls pudb.debugger:Debugger --pdb --capture=no"
    export TERM=xterm-256color
fi
echo "${PYTEST_ARGS}"

pytest ${PYTEST_ARGS}
