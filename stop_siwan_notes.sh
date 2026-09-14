#!/usr/bin/env bash
PORT="${SIWAN_PORT:-${FLATNOTES_PORT:-8090}}"
PID=$(lsof -t -i :${PORT} 2>/dev/null)
if [ -n "$PID" ]; then
    echo "正在停止运行在端口 ${PORT} 的 SiWan_notes (PID: $PID)..."
    kill -9 $PID 2>/dev/null
    echo "✓ 已停止。"
else
    echo "未发现运行在端口 ${PORT} 的 SiWan_notes 进程。"
fi
