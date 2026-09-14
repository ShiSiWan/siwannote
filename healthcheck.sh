#!/bin/sh

PORT="${SIWAN_PORT:-${FLATNOTES_PORT:-8080}}"
PREFIX="${SIWAN_PATH_PREFIX:-${FLATNOTES_PATH_PREFIX:-}}"

curl -f http://localhost:${PORT}${PREFIX}/health || exit 1
