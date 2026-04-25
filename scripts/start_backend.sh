#!/bin/bash

# 启动后端服务
echo "Starting backend server..."

# 切换到 backend 目录
cd "$(dirname "$0")/../backend" || exit 1

# 使用 uv 运行 uvicorn
if command -v uv &> /dev/null; then
    echo "Using uv to run uvicorn..."
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "uv not found, trying with python..."
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi
