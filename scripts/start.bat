@echo off
REM Windows批处理启动脚本

echo 启动时间序列洞察助手 API 服务...

REM 检查是否安装了uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到uv包管理器，请先安装uv
    echo 安装命令: pip install uv
    pause
    exit /b 1
)

REM 激活虚拟环境并启动服务
echo 使用uv运行开发服务器...
uv run python scripts/start_dev.py

pause
