"""
时间序列洞察助手 FastAPI 服务

提供时间序列分析的RESTful API接口，支持：
- 数据上传和分析
- 模型识别和参数估计
- 预测和可视化
- 结果导出
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

# 导入项目模块
from time_series_insight import TimeSeriesInsight, analyze_time_series

# 导入中间件
from middleware.error_handlers import setup_error_handlers
from middleware.logging_middleware import LoggingMiddleware, setup_logging
from middleware.rate_limiting import RateLimitingMiddleware

# 设置日志配置
setup_logging()
logger = logging.getLogger(__name__)

# 创建临时文件目录
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

# 创建输出目录
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("时间序列洞察助手 API 服务启动")
    yield
    # 关闭时
    logger.info("时间序列洞察助手 API 服务关闭")
    # 清理临时文件
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


# 创建FastAPI应用
app = FastAPI(
    title="时间序列洞察助手 API",
    description="智能的时间序列分析服务，提供自动模型识别、参数估计和可视化诊断功能",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

# 添加速率限制中间件
app.add_middleware(
    RateLimitingMiddleware,
    calls=100,  # 每分钟100次请求
    period=60,
    exclude_paths=["/docs", "/redoc", "/openapi.json", "/health"]
)

# 挂载静态文件目录
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# 设置错误处理器
setup_error_handlers(app)


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "时间序列洞察助手 API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": [
            "时间序列数据分析",
            "自动模型识别",
            "参数估计",
            "模型评估",
            "预测功能",
            "可视化图表"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "time-series-insight-assistant"}


# 导入路由模块
from routes import analysis, upload, visualization, models

# 注册路由
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["分析"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["数据上传"])
app.include_router(visualization.router, prefix="/api/v1/visualization", tags=["可视化"])
app.include_router(models.router, prefix="/api/v1/models", tags=["模型"])


if __name__ == "__main__":
    # 开发环境启动
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
