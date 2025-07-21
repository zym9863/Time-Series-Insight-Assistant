# GitHub Actions Docker 发布工作流程

## 概述

已为项目添加了自动化的Docker镜像构建和发布功能，通过GitHub Actions实现CI/CD流程。

## 新增文件

1. **`.github/workflows/docker-publish.yml`** - GitHub Actions工作流程文件
2. **`docs/GITHUB_ACTIONS_SETUP.md`** - 详细的设置和使用指南

## 主要功能

### 🔄 自动化构建
- 推送到 `main` 或 `develop` 分支时自动触发
- 创建版本标签（如 `v1.0.0`）时自动发布
- 支持手动触发构建

### 🐳 多注册表发布
- **GitHub Packages**: `ghcr.io/zym9863/time-series-insight-assistant`
- **Docker Hub**: 需要配置您的Docker Hub凭据

### 🏗️ 多平台支持
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64)

### 🔒 安全特性
- 使用Trivy进行容器安全扫描
- 将安全扫描结果上传到GitHub Security标签
- 仅在推送时发布镜像（PR不会发布）

### 🏷️ 智能标签
- `latest`: 最新的main分支版本
- `v1.0.0`: 语义化版本标签
- `main`, `develop`: 分支特定标签
- `main-abc123`: 分支+提交哈希标签

## 快速开始

### 1. 设置Docker Hub Secrets

在GitHub仓库设置中添加以下secrets：

- `DOCKERHUB_USERNAME`: 您的Docker Hub用户名
- `DOCKERHUB_TOKEN`: Docker Hub访问令牌

### 2. 使用预构建镜像

```bash
# 从GitHub Packages拉取
docker pull ghcr.io/zym9863/time-series-insight-assistant:latest

# 运行容器
docker run -p 8000:8000 ghcr.io/zym9863/time-series-insight-assistant:latest
```

### 3. 创建版本发布

```bash
# 创建并推送版本标签
git tag v1.0.0
git push origin v1.0.0
```

这将自动：
- 构建多平台镜像
- 发布到两个注册表
- 运行安全扫描
- 测试镜像
- 创建GitHub Release

## 相关文档

- [GitHub Actions 设置指南](./docs/GITHUB_ACTIONS_SETUP.md) - 详细的配置和使用说明
- [Docker 部署指南](./docs/DOCKER_DEPLOYMENT.md) - 已更新，包含预构建镜像的使用方法

## 工作流程状态

可以在仓库的 "Actions" 标签中查看工作流程的执行状态和日志。

## 故障排除

如果遇到问题，请检查：

1. Docker Hub secrets是否正确设置
2. 构建日志中的错误信息
3. Dockerfile是否有语法错误
4. 依赖项是否可以正常安装

## 贡献

如果您想改进工作流程，请：

1. Fork 仓库
2. 创建feature分支
3. 修改 `.github/workflows/docker-publish.yml`
4. 提交Pull Request

---

**注意**: 首次运行可能需要一些时间来构建和缓存依赖项。后续构建会更快，因为使用了GitHub Actions缓存。
