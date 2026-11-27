#!/bin/bash
SCRIPT_DIR=$(dirname $(readlink -f $0))
set -e

rm -rf ${SCRIPT_DIR}/build/*
rm -f ${SCRIPT_DIR}/dist/*.whl

source ${SCRIPT_DIR}/.venv/bin/activate
uv build --wheel
uv pip uninstall python-internal-inspector
uv pip install ${SCRIPT_DIR}/dist/*.whl
pytest tests -v
