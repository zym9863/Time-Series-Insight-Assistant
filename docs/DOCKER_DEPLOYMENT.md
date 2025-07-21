# Docker 部署指南

本文档介绍如何使用Docker部署时间序列洞察助手FastAPI服务。

## 📋 前提条件

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 2GB 可用内存
- 至少 1GB 可用磁盘空间

## 🚀 快速开始

### 1. 克隆项目并进入目录

```bash
git clone https://github.com/zym9863/Time-Series-Insight-Assistant.git
cd Time-Series-Insight-Assistant
```

### 2. 构建并运行服务

```bash
# 方法一：使用部署脚本（推荐）
chmod +x scripts/docker-deploy.sh
./scripts/docker-deploy.sh --build --run

# 方法二：使用Docker Compose
docker-compose up --build -d
```

### 3. 验证服务

访问以下地址验证服务是否正常运行：

- API服务: http://localhost:8000
- 健康检查: http://localhost:8000/health
- API文档: http://localhost:8000/docs

## 🐳 Docker 镜像详情

### 镜像特性

- **基础镜像**: Python 3.11-slim
- **包管理器**: uv (超快的Python包管理器)
- **多阶段构建**: 优化镜像大小
- **安全性**: 非root用户运行
- **健康检查**: 内置服务健康监控

### 镜像大小优化

- 使用slim基础镜像
- 多阶段构建分离构建和运行环境
- 移除不必要的开发依赖
- 清理包管理器缓存

## ⚙️ 配置选项

### 环境变量

在`docker-compose.yml`中可以配置以下环境变量：

```yaml
environment:
  - PYTHONPATH=/app
  - UVICORN_HOST=0.0.0.0
  - UVICORN_PORT=8000
  - UVICORN_WORKERS=4
  - LOG_LEVEL=info
```

### 端口配置

默认服务运行在8000端口，可以在`docker-compose.yml`中修改：

```yaml
ports:
  - "8080:8000"  # 将服务映射到主机的8080端口
```

### 资源限制

```yaml
deploy:
  resources:
    limits:
      memory: 1G      # 最大内存使用量
      cpus: '1.0'     # 最大CPU使用量
    reservations:
      memory: 512M    # 预留内存
      cpus: '0.5'     # 预留CPU
```

## 📁 数据持久化

项目使用卷挂载来持久化数据：

```yaml
volumes:
  - ./data:/app/data:ro        # 只读数据目录
  - ./uploads:/app/uploads     # 上传文件目录
  - ./outputs:/app/outputs     # 输出结果目录
  - ./logs:/app/logs          # 日志目录
```

## 🛠️ 部署脚本使用

`scripts/docker-deploy.sh` 提供了便捷的部署管理功能：

### 基本用法

```bash
# 显示帮助
./scripts/docker-deploy.sh --help

# 构建镜像
./scripts/docker-deploy.sh --build

# 运行服务
./scripts/docker-deploy.sh --run

# 构建并运行
./scripts/docker-deploy.sh --build --run

# 查看日志
./scripts/docker-deploy.sh --logs

# 停止服务
./scripts/docker-deploy.sh --stop

# 停止并删除容器
./scripts/docker-deploy.sh --down

# 清理Docker资源
./scripts/docker-deploy.sh --clean
```

### 高级选项

```bash
# 包含Redis缓存
./scripts/docker-deploy.sh --run --with-redis

# 包含PostgreSQL数据库
./scripts/docker-deploy.sh --run --with-db

# 开发模式构建
./scripts/docker-deploy.sh --build --dev
```

## 🔧 扩展服务

### 添加Redis缓存

```bash
# 启动包含Redis的服务
docker-compose --profile with-redis up -d

# 或使用脚本
./scripts/docker-deploy.sh --run --with-redis
```

### 添加PostgreSQL数据库

```bash
# 启动包含数据库的服务
docker-compose --profile with-db up -d

# 或使用脚本
./scripts/docker-deploy.sh --run --with-db
```

## 🔍 监控和日志

### 查看服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f time-series-api

# 使用脚本查看日志
./scripts/docker-deploy.sh --logs
```

### 健康检查

服务内置健康检查，可以通过以下方式查看：

```bash
# 检查容器健康状态
docker ps

# 手动测试健康检查端点
curl http://localhost:8000/health
```

## 🚀 生产环境部署

### 1. 环境准备

```bash
# 克隆代码
git clone https://github.com/zym9863/Time-Series-Insight-Assistant.git
cd Time-Series-Insight-Assistant

# 设置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件设置生产环境配置
```

### 2. 生产环境构建

```bash
# 构建生产镜像
docker build --target production -t time-series-insight:prod .

# 或使用 docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### 3. 反向代理配置 (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🛠️ 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :8000
   # 或修改docker-compose.yml中的端口映射
   ```

2. **权限问题**
   ```bash
   # 确保目录权限正确
   sudo chown -R $USER:$USER uploads outputs logs
   ```

3. **内存不足**
   ```bash
   # 检查Docker内存限制
   docker system df
   # 清理未使用的资源
   ./scripts/docker-deploy.sh --clean
   ```

### 调试模式

```bash
# 以调试模式运行容器
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd):/app \
  time-series-insight:latest \
  /bin/bash

# 在容器内手动启动服务进行调试
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 性能优化

### 1. 多进程部署

在生产环境中，Docker会自动使用4个worker进程。可以根据服务器配置调整：

```yaml
# 在docker-compose.yml中修改启动命令
command: ["/bin/uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

### 2. 资源监控

```bash
# 监控容器资源使用
docker stats time-series-insight-api

# 查看详细信息
docker inspect time-series-insight-api
```

## 🔄 更新和维护

### 更新服务

```bash
# 拉取最新代码
git pull origin main

# 重新构建并部署
./scripts/docker-deploy.sh --down --build --run
```

### 备份数据

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz uploads outputs logs

# 备份数据库（如果使用PostgreSQL）
docker exec time-series-postgres pg_dump -U timeseries_user timeseries > backup.sql
```

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 查看日志: `./scripts/docker-deploy.sh --logs`
2. 检查服务状态: `docker-compose ps`
3. 查看健康检查: `curl http://localhost:8000/health`
4. 提交Issue到项目仓库

---

## 🎯 最佳实践

1. **定期更新**: 定期更新基础镜像和依赖包
2. **监控资源**: 监控内存和CPU使用情况
3. **日志管理**: 定期清理和轮转日志文件
4. **备份策略**: 建立定期备份机制
5. **安全更新**: 及时应用安全补丁

通过遵循本指南，您可以安全、高效地部署时间序列洞察助手服务。
