# 使用Python 3.11官方镜像作为基础镜像
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_CACHE_DIR=/app/.uv-cache

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制uv配置文件和README（hatchling需要）
COPY pyproject.toml uv.lock README.md ./

# 安装Python依赖
RUN uv sync --frozen --no-cache

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/uploads /app/outputs /app/logs /app/.uv-cache

# 设置权限
RUN chmod +x /app/scripts/start.sh || true

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["/bin/uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# 多阶段构建 - 生产环境
FROM base as production

# 安装生产环境依赖并移除开发依赖
RUN uv sync --frozen --no-dev --no-cache

# 设置非root用户
RUN groupadd -r appuser && useradd -r -g appuser -m appuser
# 创建uv缓存目录并设置权限
RUN mkdir -p /home/appuser/.cache/uv && \
    chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 生产环境启动命令
CMD ["/bin/uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
