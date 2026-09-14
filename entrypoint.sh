#!/bin/sh

[ "$EXEC_TOOL" ] || EXEC_TOOL=gosu
SIWAN_HOST="${SIWAN_HOST:-${FLATNOTES_HOST:-0.0.0.0}}"
SIWAN_PORT="${SIWAN_PORT:-${FLATNOTES_PORT:-8080}}"
SIWAN_PATH="${SIWAN_PATH:-${FLATNOTES_PATH:-/data}}"

set -e

echo "\
======================================
====== Welcome to SiWan_notes ========
======================================

  SLAM & KNOWLEDGE LAB

──────────────────────────────────────
"

siwan_command="python -m \
                  uvicorn \
                  main:app \
                  --app-dir server \
                  --host ${SIWAN_HOST} \
                  --port ${SIWAN_PORT} \
                  --proxy-headers \
                  --forwarded-allow-ips '*'"

if [ `id -u` -eq 0 ] && [ `id -g` -eq 0 ]; then
    echo Setting file permissions...
    chown -R ${PUID}:${PGID} ${SIWAN_PATH}

    echo Starting SiWan_notes as user ${PUID}...
    exec ${EXEC_TOOL} ${PUID}:${PGID} ${siwan_command}

else
    echo "A user was set by docker, skipping file permission changes."
    echo Starting SiWan_notes as user $(id -u)...
    exec ${siwan_command}
fi
