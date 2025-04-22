#!/bin/bash

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/web_ui.py"

echo "查找运行中的 $SCRIPT_PATH 进程..."
PIDS=$(ps aux | grep "[p]ython $SCRIPT_PATH" | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "发现进程 PID: $PIDS，准备终止..."
    for PID in $PIDS; do
        kill -9 "$PID"
        echo "已终止进程 PID=$PID"
    done
    echo "✅ 所有相关进程已终止。"
else
    echo "没有发现 $SCRIPT_PATH 的运行进程。"
fi