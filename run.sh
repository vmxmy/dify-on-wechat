#!/bin/bash

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/web_ui.py"
LOG_FILE="$SCRIPT_DIR/run.log"
CONDA_ENV="dify-on-wechat"

# 初始化 conda 环境
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 激活环境
echo "激活 conda 环境：$CONDA_ENV"
conda activate "$CONDA_ENV"

# 查找已有进程
echo "检查是否已有 $SCRIPT_PATH 正在运行..."
PIDS=$(ps aux | grep "[p]ython $SCRIPT_PATH" | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "发现进程 PID: $PIDS，准备终止..."
    for PID in $PIDS; do
        kill -9 "$PID"
        echo "已终止进程 PID=$PID"
    done
else
    echo "未发现旧进程，无需终止。"
fi

# 启动新进程
echo "启动新的 $SCRIPT_PATH 进程..."
nohup python "$SCRIPT_PATH" > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "✅ 启动完成，PID=$NEW_PID，日志写入 $LOG_FILE"
tail -f "$LOG_FILE" -n 50
