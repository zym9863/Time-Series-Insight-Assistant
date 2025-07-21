# Docker 部署工作流程设置指南

这个文档说明如何为 GitHub Actions Docker 发布工作流程设置必要的 secrets。

## 必需的 GitHub Secrets

在使用 Docker 发布工作流程之前，您需要在 GitHub 仓库中设置以下 secrets：

### 1. Docker Hub Secrets

1. **DOCKERHUB_USERNAME**: 您的 Docker Hub 用户名
2. **DOCKERHUB_TOKEN**: Docker Hub 访问令牌

#### 创建 Docker Hub 访问令牌：

1. 登录到 [Docker Hub](https://hub.docker.com/)
2. 点击右上角的用户名，选择 "Account Settings"
3. 选择 "Security" 标签
4. 点击 "New Access Token"
5. 输入描述（如 "GitHub Actions"）
6. 选择权限（推荐选择 "Public Repo"）
7. 点击 "Generate"
8. 复制生成的令牌（只会显示一次）

### 2. 在 GitHub 仓库中添加 Secrets

1. 进入您的 GitHub 仓库
2. 点击 "Settings" 标签
3. 在左侧菜单中选择 "Secrets and variables" > "Actions"
4. 点击 "New repository secret"
5. 添加以下 secrets：
   - Name: `DOCKERHUB_USERNAME`，Value: 您的 Docker Hub 用户名
   - Name: `DOCKERHUB_TOKEN`，Value: 您的 Docker Hub 访问令牌

## 工作流程功能

### 触发条件

工作流程在以下情况下会触发：

- 推送到 `main` 或 `develop` 分支
- 创建以 `v` 开头的标签（如 `v1.0.0`）
- 向 `main` 分支提交 Pull Request
- 手动触发（workflow_dispatch）

### 构建目标

- **多平台支持**: 支持 `linux/amd64` 和 `linux/arm64` 架构
- **多注册表**: 同时推送到 GitHub Packages 和 Docker Hub
- **缓存优化**: 使用 GitHub Actions 缓存来加速构建

### 标签策略

工作流程会自动生成以下标签：

- `latest`: 最新的 main 分支版本
- `main`: main 分支的最新提交
- `develop`: develop 分支的最新提交
- `v1.0.0`: 语义化版本标签
- `v1.0`: 主版本和次版本
- `v1`: 主版本
- `main-abc123`: 分支名和短提交哈希

### 安全扫描

- 使用 Trivy 进行容器安全扫描
- 将扫描结果上传到 GitHub Security 标签

### 镜像测试

- 自动测试构建的镜像
- 验证健康检查端点
- 验证 API 文档端点

## 使用示例

### 从 GitHub Packages 拉取镜像

```bash
# 拉取最新版本
docker pull ghcr.io/zym9863/time-series-insight-assistant:latest

# 拉取特定版本
docker pull ghcr.io/zym9863/time-series-insight-assistant:v1.0.0

# 运行容器
docker run -p 8000:8000 ghcr.io/zym9863/time-series-insight-assistant:latest
```

### 从 Docker Hub 拉取镜像

```bash
# 拉取最新版本（需要替换为您的 Docker Hub 用户名）
docker pull your-dockerhub-username/time-series-insight-assistant:latest

# 拉取特定版本
docker pull your-dockerhub-username/time-series-insight-assistant:v1.0.0

# 运行容器
docker run -p 8000:8000 your-dockerhub-username/time-series-insight-assistant:latest
```

### 使用 Docker Compose

您也可以更新 `docker-compose.yml` 文件来使用发布的镜像：

```yaml
version: '3.8'

services:
  app:
    image: ghcr.io/zym9863/time-series-insight-assistant:latest
    # 或者使用 Docker Hub 镜像
    # image: your-dockerhub-username/time-series-insight-assistant:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./logs:/app/logs
```

## 发布流程

### 自动发布

1. **开发版本**: 推送到 `develop` 分支会自动构建并标记为 `develop`
2. **主版本**: 推送到 `main` 分支会自动构建并标记为 `latest`
3. **版本发布**: 创建版本标签（如 `v1.0.0`）会触发完整的发布流程，包括创建 GitHub Release

### 手动发布

您也可以通过以下方式手动触发工作流程：

1. 进入 GitHub 仓库的 "Actions" 标签
2. 选择 "Docker Publish" 工作流程
3. 点击 "Run workflow"
4. 选择分支并点击 "Run workflow"

## 故障排除

### 常见问题

1. **认证失败**: 确保 Docker Hub secrets 设置正确
2. **权限错误**: 确保 Docker Hub 令牌有足够的权限
3. **构建失败**: 检查 Dockerfile 和依赖项是否正确

### 调试提示

- 查看 Actions 标签中的构建日志
- 检查 secrets 是否正确设置
- 确保 Docker Hub 仓库存在（如果需要）

## 最佳实践

1. **使用语义化版本**: 使用 `v1.0.0` 格式的标签
2. **定期更新基础镜像**: 保持 Dockerfile 中的基础镜像为最新版本
3. **监控安全扫描**: 定期检查 Security 标签中的漏洞报告
4. **测试镜像**: 在部署前先本地测试构建的镜像
