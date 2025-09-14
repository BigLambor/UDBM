#!/bin/bash

# UDBM 项目配置文件
# 此文件定义了项目的默认配置

# 项目信息
PROJECT_NAME="UDBM"
PROJECT_VERSION="1.0.0"
PROJECT_DESCRIPTION="统一数据库管理平台"

# 服务端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 数据库配置
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="udbm_user"
POSTGRES_PASSWORD="udbm_password"
POSTGRES_DB="udbm_db"

# Redis配置
REDIS_HOST="localhost"
REDIS_PORT=6379

# JWT配置
SECRET_KEY="dev-secret-key-change-in-production"
JWT_EXPIRE_MINUTES=30

# 启动选项
DOCKER_MODE=false
SKIP_CHECKS=false
VERBOSE=false

# 依赖检查配置
REQUIRED_COMMANDS=("python3" "node" "npm" "docker" "docker-compose")
REQUIRED_PYTHON_PACKAGES=("fastapi" "uvicorn" "sqlalchemy" "pydantic")
REQUIRED_NODE_PACKAGES=("react" "react-dom" "axios")

# 颜色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 目录配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/udbm-backend"
FRONTEND_DIR="$PROJECT_ROOT/udbm-frontend"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/logs"

# PID文件
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
DOCKER_COMPOSE_PID_FILE="$PID_DIR/docker-compose.pid"

# 日志文件
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Docker配置
DOCKER_COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"
DOCKER_PROJECT_NAME="udbm"

# 超时配置
STARTUP_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5

# 网络配置
BACKEND_URL="http://localhost:$BACKEND_PORT"
FRONTEND_URL="http://localhost:$FRONTEND_PORT"
API_DOCS_URL="$BACKEND_URL/docs"

# 导出所有配置变量
export PROJECT_NAME PROJECT_VERSION PROJECT_DESCRIPTION
export BACKEND_PORT FRONTEND_PORT
export POSTGRES_HOST POSTGRES_PORT POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB
export REDIS_HOST REDIS_PORT
export SECRET_KEY JWT_EXPIRE_MINUTES
export DOCKER_MODE SKIP_CHECKS VERBOSE
export PROJECT_ROOT BACKEND_DIR FRONTEND_DIR PID_DIR LOG_DIR
export BACKEND_PID_FILE FRONTEND_PID_FILE DOCKER_COMPOSE_PID_FILE
export BACKEND_LOG FRONTEND_LOG
export DOCKER_COMPOSE_FILE DOCKER_PROJECT_NAME
export STARTUP_TIMEOUT HEALTH_CHECK_INTERVAL
export BACKEND_URL FRONTEND_URL API_DOCS_URL

# 颜色函数
log_info() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] INFO:${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"
}

log_debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[$(date '+%H:%M:%S')] DEBUG:${NC} $1"
    fi
}

# 配置检查函数
check_config() {
    log_debug "检查配置文件完整性..."

    # 检查必需的目录
    local dirs=("$BACKEND_DIR" "$FRONTEND_DIR")
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log_error "必需目录不存在: $dir"
            return 1
        fi
    done

    # 检查必需的文件
    local files=("$BACKEND_DIR/requirements.txt" "$FRONTEND_DIR/package.json")
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "必需文件不存在: $file"
            return 1
        fi
    done

    log_debug "配置文件检查通过"
    return 0
}

# 如果直接运行此脚本，显示配置信息
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "${CYAN}=== UDBM 项目配置信息 ===${NC}"
    echo "项目名称: $PROJECT_NAME"
    echo "项目版本: $PROJECT_VERSION"
    echo "后端端口: $BACKEND_PORT"
    echo "前端端口: $FRONTEND_PORT"
    echo "数据库: $POSTGRES_DB@$POSTGRES_HOST:$POSTGRES_PORT"
    echo "Redis: $REDIS_HOST:$REDIS_PORT"
    echo "Docker模式: $DOCKER_MODE"
    echo "跳过检查: $SKIP_CHECKS"
    echo "详细输出: $VERBOSE"
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo "  前端: $FRONTEND_URL"
    echo "  后端API: $BACKEND_URL"
    echo "  API文档: $API_DOCS_URL"
fi
