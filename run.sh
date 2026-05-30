#!/bin/bash
# Cargo Tracker - 启动脚本
# 用法: ./run.sh

set -e

# 设置环境变量
export MINIMAX_API_KEY="${MINIMAX_API_KEY:-}"

# 数据目录（挂载到 NAS 持久化存储）
DATA_DIR="/volume1/docker/cargo-tracker/data"
mkdir -p "$DATA_DIR"

echo "========================================"
echo "📦 Cargo Tracker - 海运清单管理"
echo "========================================"
echo "数据目录: $DATA_DIR"
echo "访问地址: http://你的NASIP:5180"
echo ""

# 检查 API Key
if [ -z "$MINIMAX_API_KEY" ]; then
    echo "⚠️  警告: MINIMAX_API_KEY 未设置，OCR 功能将无法使用"
    echo "   请在 .env 文件中设置或运行: export MINIMAX_API_KEY=你的密钥"
fi

# 启动 Docker 容器
docker run -d \
    --name cargo-tracker \
    --restart unless-stopped \
    -p 5180:5180 \
    -v "$DATA_DIR:/data" \
    -v "$(pwd)/.env:/app/.env" \
    -e MINIMAX_API_KEY \
    ghcr.io/devinidea/cargo-tracker:latest

echo "✅ 启动成功!"
echo "   停止: docker stop cargo-tracker"
echo "   日志: docker logs -f cargo-tracker"
