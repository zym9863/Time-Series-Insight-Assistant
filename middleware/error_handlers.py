"""
全局错误处理器
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime
from typing import Union

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI):
    """设置全局错误处理器"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理器"""
        logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail} - URL: {request.url}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP错误",
                "detail": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Starlette HTTP异常处理器"""
        logger.warning(f"Starlette HTTP异常: {exc.status_code} - {exc.detail} - URL: {request.url}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP错误",
                "detail": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """请求验证错误处理器"""
        logger.warning(f"请求验证错误: {exc.errors()} - URL: {request.url}")
        
        # 格式化验证错误信息
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "请求验证失败",
                "detail": "请求参数不符合要求",
                "validation_errors": error_details,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """值错误处理器"""
        logger.error(f"值错误: {str(exc)} - URL: {request.url}")
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "参数错误",
                "detail": str(exc),
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        """文件未找到错误处理器"""
        logger.error(f"文件未找到: {str(exc)} - URL: {request.url}")
        
        return JSONResponse(
            status_code=404,
            content={
                "error": "文件未找到",
                "detail": str(exc),
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        """权限错误处理器"""
        logger.error(f"权限错误: {str(exc)} - URL: {request.url}")
        
        return JSONResponse(
            status_code=403,
            content={
                "error": "权限不足",
                "detail": "没有足够的权限执行此操作",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理器"""
        logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)} - URL: {request.url}")
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        # 在开发环境中返回详细错误信息，生产环境中返回通用错误信息
        import os
        is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
        
        if is_development:
            detail = f"{type(exc).__name__}: {str(exc)}"
            traceback_info = traceback.format_exc()
        else:
            detail = "服务器内部错误，请稍后重试"
            traceback_info = None
        
        content = {
            "error": "内部服务器错误",
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
        
        if traceback_info:
            content["traceback"] = traceback_info
        
        return JSONResponse(
            status_code=500,
            content=content
        )


class CustomHTTPException(HTTPException):
    """自定义HTTP异常类"""
    
    def __init__(
        self,
        status_code: int,
        detail: str = None,
        error_code: str = None,
        headers: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


def raise_http_error(
    status_code: int,
    message: str,
    error_code: str = None,
    headers: dict = None
):
    """抛出HTTP错误的便捷函数"""
    raise CustomHTTPException(
        status_code=status_code,
        detail=message,
        error_code=error_code,
        headers=headers
    )
