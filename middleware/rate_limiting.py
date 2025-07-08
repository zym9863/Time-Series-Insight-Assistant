"""
速率限制中间件
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Callable
from collections import defaultdict, deque
import asyncio


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        per_ip: bool = True,
        exclude_paths: list = None
    ):
        """
        初始化速率限制中间件
        
        Args:
            app: FastAPI应用实例
            calls: 允许的调用次数
            period: 时间窗口（秒）
            per_ip: 是否按IP限制
            exclude_paths: 排除的路径列表
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.per_ip = per_ip
        self.exclude_paths = exclude_paths or []
        
        # 存储请求记录
        self.requests: Dict[str, deque] = defaultdict(deque)
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_old_requests())
    
    async def dispatch(self, request: Request, call_next: Callable):
        """处理请求速率限制"""
        
        # 检查是否在排除路径中
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 获取客户端标识
        client_id = self._get_client_id(request)
        
        # 检查速率限制
        if self._is_rate_limited(client_id):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "请求过于频繁",
                    "detail": f"每{self.period}秒最多允许{self.calls}次请求",
                    "retry_after": self._get_retry_after(client_id)
                }
            )
        
        # 记录请求
        self._record_request(client_id)
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制头部
        remaining = self._get_remaining_requests(client_id)
        reset_time = self._get_reset_time(client_id)
        
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        if self.per_ip:
            # 尝试获取真实IP
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip
            
            if hasattr(request.client, "host"):
                return request.client.host
            
            return "unknown"
        else:
            # 可以基于用户ID或API密钥等其他标识
            return "global"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        window_start = now - self.period
        
        # 清理过期请求
        while self.requests[client_id] and self.requests[client_id][0] < window_start:
            self.requests[client_id].popleft()
        
        # 检查是否超过限制
        return len(self.requests[client_id]) >= self.calls
    
    def _record_request(self, client_id: str):
        """记录请求"""
        now = time.time()
        self.requests[client_id].append(now)
    
    def _get_remaining_requests(self, client_id: str) -> int:
        """获取剩余请求次数"""
        return max(0, self.calls - len(self.requests[client_id]))
    
    def _get_reset_time(self, client_id: str) -> int:
        """获取重置时间"""
        if not self.requests[client_id]:
            return int(time.time() + self.period)
        
        oldest_request = self.requests[client_id][0]
        return int(oldest_request + self.period)
    
    def _get_retry_after(self, client_id: str) -> int:
        """获取重试等待时间"""
        if not self.requests[client_id]:
            return 0
        
        oldest_request = self.requests[client_id][0]
        retry_after = oldest_request + self.period - time.time()
        return max(0, int(retry_after))
    
    async def _cleanup_old_requests(self):
        """定期清理过期请求记录"""
        while True:
            await asyncio.sleep(60)  # 每分钟清理一次
            
            now = time.time()
            window_start = now - self.period
            
            # 清理所有客户端的过期请求
            for client_id in list(self.requests.keys()):
                while (self.requests[client_id] and 
                       self.requests[client_id][0] < window_start):
                    self.requests[client_id].popleft()
                
                # 如果队列为空，删除该客户端记录
                if not self.requests[client_id]:
                    del self.requests[client_id]


class AdaptiveRateLimitingMiddleware(BaseHTTPMiddleware):
    """自适应速率限制中间件"""
    
    def __init__(
        self,
        app,
        base_calls: int = 100,
        base_period: int = 60,
        burst_calls: int = 200,
        burst_period: int = 10
    ):
        """
        初始化自适应速率限制中间件
        
        Args:
            app: FastAPI应用实例
            base_calls: 基础调用次数
            base_period: 基础时间窗口
            burst_calls: 突发调用次数
            burst_period: 突发时间窗口
        """
        super().__init__(app)
        self.base_calls = base_calls
        self.base_period = base_period
        self.burst_calls = burst_calls
        self.burst_period = burst_period
        
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next: Callable):
        """处理自适应速率限制"""
        
        client_id = self._get_client_id(request)
        
        # 检查突发限制
        if self._is_burst_limited(client_id):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "突发请求过多",
                    "detail": f"每{self.burst_period}秒最多允许{self.burst_calls}次请求"
                }
            )
        
        # 检查基础限制
        if self._is_base_limited(client_id):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "请求过于频繁",
                    "detail": f"每{self.base_period}秒最多允许{self.base_calls}次请求"
                }
            )
        
        # 记录请求
        self._record_request(client_id)
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _is_burst_limited(self, client_id: str) -> bool:
        """检查突发限制"""
        now = time.time()
        burst_window_start = now - self.burst_period
        
        # 计算突发窗口内的请求数
        burst_count = sum(
            1 for req_time in self.requests[client_id]
            if req_time >= burst_window_start
        )
        
        return burst_count >= self.burst_calls
    
    def _is_base_limited(self, client_id: str) -> bool:
        """检查基础限制"""
        now = time.time()
        base_window_start = now - self.base_period
        
        # 清理过期请求
        while (self.requests[client_id] and 
               self.requests[client_id][0] < base_window_start):
            self.requests[client_id].popleft()
        
        return len(self.requests[client_id]) >= self.base_calls
    
    def _record_request(self, client_id: str):
        """记录请求"""
        now = time.time()
        self.requests[client_id].append(now)
