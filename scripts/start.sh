#!/bin/bash
# Linux/macOS启动脚本

echo "启动时间序列洞察助手 API 服务..."

# 检查是否安装了uv
if ! command -v uv &> /dev/null; then
    echo "错误: 未找到uv包管理器，请先安装uv"
    echo "安装命令: pip install uv"
    exit 1
fi

# 设置脚本权限
chmod +x scripts/start_dev.py
chmod +x scripts/start_prod.py

# 检查参数
if [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    echo "使用uv运行生产服务器..."
    uv run python scripts/start_prod.py
else
    echo "使用uv运行开发服务器..."
    uv run python scripts/start_dev.py
fi
