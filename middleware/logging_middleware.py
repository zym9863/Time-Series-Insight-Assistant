"""
日志中间件
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和响应日志"""
        
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        if self.log_requests:
            client_ip = self._get_client_ip(request)
            logger.info(
                f"[{request_id}] 请求开始 - "
                f"方法: {request.method} "
                f"路径: {request.url.path} "
                f"查询参数: {dict(request.query_params)} "
                f"客户端IP: {client_ip}"
            )
        
        # 将请求ID添加到请求状态中
        request.state.request_id = request_id
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            if self.log_responses:
                logger.info(
                    f"[{request_id}] 请求完成 - "
                    f"状态码: {response.status_code} "
                    f"处理时间: {process_time:.3f}s"
                )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常
            logger.error(
                f"[{request_id}] 请求异常 - "
                f"异常类型: {type(e).__name__} "
                f"异常信息: {str(e)} "
                f"处理时间: {process_time:.3f}s"
            )
            
            # 重新抛出异常
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 尝试从各种头部获取真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """监控请求性能"""
        
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录慢请求
        if process_time > self.slow_request_threshold:
            logger.warning(
                f"慢请求检测 - "
                f"方法: {request.method} "
                f"路径: {request.url.path} "
                f"处理时间: {process_time:.3f}s "
                f"阈值: {self.slow_request_threshold}s"
            )
        
        return response


def setup_logging():
    """设置日志配置"""

    # 创建日志目录
    import os
    os.makedirs("logs", exist_ok=True)

    # 创建日志格式
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )

    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # 控制台输出
            logging.FileHandler("logs/app.log", encoding="utf-8")  # 文件输出
        ]
    )

    # 设置特定模块的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
