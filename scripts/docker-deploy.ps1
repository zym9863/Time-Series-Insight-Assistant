# Time Series Insight Assistant Docker 部署脚本 (PowerShell)
# 用法: .\scripts\docker-deploy.ps1 [选项]

param(
    [switch]$Help,
    [switch]$Build,
    [switch]$Run,
    [switch]$Stop,
    [switch]$Down,
    [switch]$Logs,
    [switch]$Clean,
    [switch]$WithRedis,
    [switch]$WithDb,
    [switch]$Dev
)

# 颜色定义
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = "Red"
        "Green" = "Green"
        "Yellow" = "Yellow"
        "Blue" = "Blue"
        "White" = "White"
    }
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

function Log-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Blue"
}

function Log-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Log-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Log-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# 显示帮助信息
function Show-Help {
    @"
Time Series Insight Assistant Docker 部署脚本 (PowerShell)

用法: .\scripts\docker-deploy.ps1 [选项]

选项:
    -Help               显示此帮助信息
    -Build              构建Docker镜像
    -Run                运行服务
    -Stop               停止服务
    -Down               停止并删除容器
    -Logs               查看日志
    -Clean              清理未使用的Docker资源
    -WithRedis          包含Redis服务
    -WithDb             包含PostgreSQL数据库
    -Dev                使用开发模式构建

示例:
    .\scripts\docker-deploy.ps1 -Build -Run                    # 构建并运行服务
    .\scripts\docker-deploy.ps1 -Run -WithRedis               # 运行服务并包含Redis
    .\scripts\docker-deploy.ps1 -Stop                         # 停止服务
    .\scripts\docker-deploy.ps1 -Logs                         # 查看日志
"@
}

# 检查Docker是否安装
function Test-Docker {
    try {
        $null = docker --version
        $null = docker-compose --version
        return $true
    }
    catch {
        return $false
    }
}

# 构建镜像
function Build-Image {
    Log-Info "开始构建Docker镜像..."
    
    $target = if ($Dev) { "base" } else { "production" }
    
    if ($Dev) {
        Log-Info "使用开发模式构建"
    }
    
    try {
        docker build --target $target -t time-series-insight:latest .
        
        if ($LASTEXITCODE -eq 0) {
            Log-Success "Docker镜像构建完成"
        }
        else {
            throw "构建失败"
        }
    }
    catch {
        Log-Error "Docker镜像构建失败: $_"
        exit 1
    }
}

# 运行服务
function Start-Services {
    Log-Info "启动服务..."
    
    $composeCmd = "docker-compose up -d"
    
    if ($WithRedis) {
        $composeCmd += " --profile with-redis"
        Log-Info "包含Redis服务"
    }
    
    if ($WithDb) {
        $composeCmd += " --profile with-db"
        Log-Info "包含PostgreSQL数据库服务"
    }
    
    try {
        Invoke-Expression $composeCmd
        
        if ($LASTEXITCODE -eq 0) {
            Log-Success "服务启动成功"
            Log-Info "API服务地址: http://localhost:8000"
            Log-Info "健康检查: http://localhost:8000/health"
            Log-Info "使用 '.\scripts\docker-deploy.ps1 -Logs' 查看日志"
        }
        else {
            throw "启动失败"
        }
    }
    catch {
        Log-Error "服务启动失败: $_"
        exit 1
    }
}

# 停止服务
function Stop-Services {
    Log-Info "停止服务..."
    try {
        docker-compose stop
        Log-Success "服务已停止"
    }
    catch {
        Log-Error "停止服务失败: $_"
    }
}

# 删除容器
function Remove-Services {
    Log-Info "停止并删除容器..."
    try {
        docker-compose down
        Log-Success "容器已删除"
    }
    catch {
        Log-Error "删除容器失败: $_"
    }
}

# 查看日志
function Show-Logs {
    Log-Info "查看服务日志 (按 Ctrl+C 退出)..."
    try {
        docker-compose logs -f time-series-api
    }
    catch {
        Log-Error "查看日志失败: $_"
    }
}

# 清理Docker资源
function Clear-Docker {
    Log-Info "清理未使用的Docker资源..."
    try {
        docker system prune -f
        docker volume prune -f
        Log-Success "清理完成"
    }
    catch {
        Log-Error "清理失败: $_"
    }
}

# 创建必要的目录
function New-Directories {
    Log-Info "创建必要的目录..."
    
    $directories = @("uploads", "outputs", "logs", "data")
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Log-Success "目录创建完成"
}

# 主函数
function Main {
    # 如果没有指定任何选项，显示帮助
    if (-not ($Build -or $Run -or $Stop -or $Down -or $Logs -or $Clean)) {
        Show-Help
        return
    }

    # 显示帮助
    if ($Help) {
        Show-Help
        return
    }

    # 检查Docker
    if (-not (Test-Docker)) {
        Log-Error "Docker 或 Docker Compose 未安装或未正确配置"
        Log-Error "请确保 Docker 和 Docker Compose 已安装并可以在命令行中使用"
        exit 1
    }

    # 创建目录
    New-Directories

    # 执行操作
    if ($Build) {
        Build-Image
    }

    if ($Run) {
        Start-Services
    }

    if ($Stop) {
        Stop-Services
    }

    if ($Down) {
        Remove-Services
    }

    if ($Logs) {
        Show-Logs
    }

    if ($Clean) {
        Clear-Docker
    }
}

# 运行主函数
Main
