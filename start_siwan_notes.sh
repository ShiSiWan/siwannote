#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check persistent custom storage path if configured
if [ -f "${SCRIPT_DIR}/.siwan_server_config.json" ]; then
    CUSTOM_PATH=$(python3 -c "import json; print(json.load(open('${SCRIPT_DIR}/.siwan_server_config.json')).get('storage_path', ''))" 2>/dev/null)
    if [ -n "$CUSTOM_PATH" ] && [ -d "$CUSTOM_PATH" ]; then
        SIWAN_PATH="$CUSTOM_PATH"
    fi
fi

export SIWAN_PATH="${SIWAN_PATH:-${FLATNOTES_PATH:-${SCRIPT_DIR}/data}}"
export SIWAN_AUTH_TYPE="${SIWAN_AUTH_TYPE:-${FLATNOTES_AUTH_TYPE:-none}}"
export SIWAN_PORT="${SIWAN_PORT:-${FLATNOTES_PORT:-8090}}"
export SIWAN_HOST="${SIWAN_HOST:-${FLATNOTES_HOST:-0.0.0.0}}"

LOG_FILE="${SCRIPT_DIR}/siwan_notes.log"

# Stop existing instance if any
PID=$(lsof -t -i :${SIWAN_PORT} 2>/dev/null)
if [ -n "$PID" ]; then
    echo "⚠️ 停止已存在的进程 (PID: $PID)..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

setsid -f env SIWAN_PATH="${SIWAN_PATH}" \
             SIWAN_AUTH_TYPE="${SIWAN_AUTH_TYPE}" \
             python3 -m uvicorn main:app \
             --app-dir server \
             --host "${SIWAN_HOST}" \
             --port "${SIWAN_PORT}" \
             --proxy-headers \
             --forwarded-allow-ips '*' </dev/null > "${LOG_FILE}" 2>&1

sleep 1.5
PID=$(lsof -t -i :${SIWAN_PORT} 2>/dev/null)
if [ -n "$PID" ]; then
    echo "=================================================="
    echo "  🚀 SiWan_notes 已成功启动并脱机驻留 (PID: ${PID})"
    echo "  📁 数据目录: ${SIWAN_PATH}"
    echo "  🌐 访问地址: http://localhost:${SIWAN_PORT}"
    echo "  📝 日志文件: ${LOG_FILE}"
    echo "=================================================="
else
    echo "❌ 启动失败，请检查日志: ${LOG_FILE}"
fi
