#!/bin/bash

# Time Series Insight Assistant Docker 部署脚本
# 用法: ./scripts/docker-deploy.sh [选项]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
Time Series Insight Assistant Docker 部署脚本

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -b, --build             构建Docker镜像
    -r, --run               运行服务
    -s, --stop              停止服务
    -d, --down              停止并删除容器
    -l, --logs              查看日志
    -c, --clean             清理未使用的Docker资源
    --with-redis            包含Redis服务
    --with-db               包含PostgreSQL数据库
    --dev                   使用开发模式构建

示例:
    $0 --build --run                    # 构建并运行服务
    $0 --run --with-redis               # 运行服务并包含Redis
    $0 --stop                          # 停止服务
    $0 --logs                          # 查看日志
EOF
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
}

# 构建镜像
build_image() {
    log_info "开始构建Docker镜像..."
    
    local target="production"
    if [[ "$DEV_MODE" == "true" ]]; then
        target="base"
        log_info "使用开发模式构建"
    fi
    
    docker build --target "$target" -t time-series-insight:latest .
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker镜像构建完成"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 运行服务
run_services() {
    log_info "启动服务..."
    
    local compose_cmd="docker-compose up -d"
    
    if [[ "$WITH_REDIS" == "true" ]]; then
        compose_cmd="$compose_cmd --profile with-redis"
        log_info "包含Redis服务"
    fi
    
    if [[ "$WITH_DB" == "true" ]]; then
        compose_cmd="$compose_cmd --profile with-db"
        log_info "包含PostgreSQL数据库服务"
    fi
    
    eval $compose_cmd
    
    if [[ $? -eq 0 ]]; then
        log_success "服务启动成功"
        log_info "API服务地址: http://localhost:8000"
        log_info "健康检查: http://localhost:8000/health"
        log_info "使用 '$0 --logs' 查看日志"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose stop
    log_success "服务已停止"
}

# 删除容器
down_services() {
    log_info "停止并删除容器..."
    docker-compose down
    log_success "容器已删除"
}

# 查看日志
view_logs() {
    log_info "查看服务日志 (按 Ctrl+C 退出)..."
    docker-compose logs -f time-series-api
}

# 清理Docker资源
clean_docker() {
    log_info "清理未使用的Docker资源..."
    docker system prune -f
    docker volume prune -f
    log_success "清理完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p uploads outputs logs data
    log_success "目录创建完成"
}

# 主函数
main() {
    local BUILD=false
    local RUN=false
    local STOP=false
    local DOWN=false
    local LOGS=false
    local CLEAN=false
    local WITH_REDIS=false
    local WITH_DB=false
    local DEV_MODE=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -b|--build)
                BUILD=true
                shift
                ;;
            -r|--run)
                RUN=true
                shift
                ;;
            -s|--stop)
                STOP=true
                shift
                ;;
            -d|--down)
                DOWN=true
                shift
                ;;
            -l|--logs)
                LOGS=true
                shift
                ;;
            -c|--clean)
                CLEAN=true
                shift
                ;;
            --with-redis)
                WITH_REDIS=true
                shift
                ;;
            --with-db)
                WITH_DB=true
                shift
                ;;
            --dev)
                DEV_MODE=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 如果没有指定任何选项，显示帮助
    if [[ "$BUILD" == false && "$RUN" == false && "$STOP" == false && "$DOWN" == false && "$LOGS" == false && "$CLEAN" == false ]]; then
        show_help
        exit 0
    fi

    # 检查Docker
    check_docker

    # 创建目录
    create_directories

    # 执行操作
    if [[ "$BUILD" == true ]]; then
        build_image
    fi

    if [[ "$RUN" == true ]]; then
        run_services
    fi

    if [[ "$STOP" == true ]]; then
        stop_services
    fi

    if [[ "$DOWN" == true ]]; then
        down_services
    fi

    if [[ "$LOGS" == true ]]; then
        view_logs
    fi

    if [[ "$CLEAN" == true ]]; then
        clean_docker
    fi
}

# 运行主函数
main "$@"
