#!/usr/bin/env python3
"""
开发环境启动脚本

用于启动开发环境的FastAPI服务
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """启动开发服务器"""
    
    # 设置环境变量
    os.environ["ENVIRONMENT"] = "development"
    
    # 创建必要的目录
    directories = ["temp_files", "outputs", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("🚀 启动时间序列洞察助手 API 开发服务器...")
    print(f"📁 项目根目录: {project_root}")
    print("🌐 服务地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("=" * 50)
    
    # 启动服务器
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root)],
        log_level="info",
        access_log=True,
        use_colors=True,
        reload_excludes=["temp_files/*", "outputs/*", "logs/*", "*.log"]
    )

if __name__ == "__main__":
    main()
