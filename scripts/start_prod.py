#!/usr/bin/env python3
"""
生产环境启动脚本

用于启动生产环境的FastAPI服务
"""

import uvicorn
import os
import sys
import multiprocessing
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_workers_count():
    """获取工作进程数量"""
    # 根据CPU核心数确定工作进程数
    cpu_count = multiprocessing.cpu_count()
    return min(cpu_count * 2 + 1, 8)  # 最多8个工作进程

def main():
    """启动生产服务器"""
    
    # 设置环境变量
    os.environ["ENVIRONMENT"] = "production"
    
    # 创建必要的目录
    directories = ["temp_files", "outputs", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # 获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", get_workers_count()))
    
    print("🚀 启动时间序列洞察助手 API 生产服务器...")
    print(f"📁 项目根目录: {project_root}")
    print(f"🌐 服务地址: http://{host}:{port}")
    print(f"👥 工作进程数: {workers}")
    print("=" * 50)
    
    # 启动服务器
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=workers,
        log_level="warning",
        access_log=False,
        use_colors=False,
        reload=False
    )

if __name__ == "__main__":
    main()
