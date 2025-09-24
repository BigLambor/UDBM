#!/bin/bash

# UDBM 项目启动脚本
# 统一数据库管理平台启动工具
# 支持本地开发和Docker部署模式

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/udbm-backend"
FRONTEND_DIR="$PROJECT_ROOT/udbm-frontend"

# 默认配置
BACKEND_PORT=8000
FRONTEND_PORT=3000
DOCKER_MODE=false
VERBOSE=false
SKIP_CHECKS=false
FORCE_CLEANUP=false
LAN_MODE=false

# 进程ID文件
PID_DIR="$PROJECT_ROOT/.pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
DOCKER_COMPOSE_PID_FILE="$PID_DIR/docker-compose.pid"

# 日志文件
LOG_DIR="$PROJECT_ROOT/logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# 函数定义

# 获取本机IP地址
get_local_ip() {
    local ip=""
    
    # 尝试多种方法获取IP地址
    if command -v ip >/dev/null 2>&1; then
        # Linux系统
        ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null)
    elif command -v ifconfig >/dev/null 2>&1; then
        # macOS/Unix系统
        ip=$(ifconfig | grep -E "inet (192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)" | head -1 | awk '{print $2}' | sed 's/addr://')
    fi
    
    # 如果上述方法都失败，尝试通过外部服务获取
    if [ -z "$ip" ]; then
        ip=$(curl -s --connect-timeout 3 ifconfig.me 2>/dev/null || curl -s --connect-timeout 3 ipinfo.io/ip 2>/dev/null || echo "127.0.0.1")
    fi
    
    # 如果仍然为空，使用默认值
    if [ -z "$ip" ]; then
        ip="127.0.0.1"
    fi
    
    echo "$ip"
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}UDBM 项目启动脚本${NC}"
    echo -e "${BLUE}用法:${NC} $0 [选项] [命令]"
    echo ""
    echo -e "${BLUE}命令:${NC}"
    echo "  start       启动项目 (默认)"
    echo "  stop        停止项目"
    echo "  restart     重启项目"
    echo "  status      查看项目状态"
    echo "  logs        查看日志"
    echo "  clean       清理临时文件和容器"
    echo ""
    echo -e "${BLUE}选项:${NC}"
    echo "  -d, --docker    使用Docker模式启动"
    echo "  -b, --backend   仅启动后端"
    echo "  -f, --frontend  仅启动前端"
    echo "  -p, --port      指定端口 (后端:8000 前端:3000)"
    echo "  -l, --lan       局域网模式启动（允许同事访问）"
    echo "  -v, --verbose   详细输出"
    echo "  -s, --skip      跳过环境检查"
    echo "  --force         强制清理占用端口的进程"
    echo "  -h, --help      显示帮助信息"
    echo ""
    echo -e "${BLUE}示例:${NC}"
    echo "  $0 start                    # 本地开发模式启动"
    echo "  $0 start --lan              # 局域网模式启动（同事可访问）"
    echo "  $0 start --docker           # Docker模式启动"
    echo "  $0 start --backend --port 8001  # 仅启动后端在8001端口"
    echo "  $0 stop                     # 停止所有服务"
    echo "  $0 logs --backend           # 查看后端日志"
}

# 记录日志
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "INFO")
            echo -e "${GREEN}[$timestamp] INFO:${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[$timestamp] WARN:${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[$timestamp] ERROR:${NC} $message"
            ;;
        "DEBUG")
            if [ "$VERBOSE" = true ]; then
                echo -e "${BLUE}[$timestamp] DEBUG:${NC} $message"
            fi
            ;;
        *)
            echo -e "${CYAN}[$timestamp] $level:${NC} $message"
            ;;
    esac
}

# 创建目录
create_directories() {
    mkdir -p "$PID_DIR" "$LOG_DIR"
}

# 检查命令是否存在
check_command() {
    local cmd="$1"
    local name="$2"

    if ! command -v "$cmd" &> /dev/null; then
        log "ERROR" "$name 未安装或不在PATH中"
        log "INFO" "请安装 $name 后重试"
        return 1
    fi
    log "DEBUG" "找到 $name: $(which $cmd)"
    return 0
}

# 检查端口是否被占用
check_port() {
    local port="$1"
    local name="$2"
    local force_clear="${3:-false}"

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        if [ "$force_clear" = true ]; then
            log "WARN" "$name 端口 $port 已被占用，正在强制清理..."
            force_kill_port $port "$name"
            return $?
        else
            log "WARN" "$name 端口 $port 已被占用"
            return 1
        fi
    fi
    log "DEBUG" "$name 端口 $port 可用"
    return 0
}

# 等待端口可用
wait_for_port() {
    local port="$1"
    local timeout="${2:-30}"
    local count=0

    log "INFO" "等待端口 $port 启动..."
    while ! nc -z localhost $port 2>/dev/null; do
        if [ $count -ge $timeout ]; then
            log "ERROR" "端口 $port 启动超时"
            return 1
        fi
        sleep 1
        ((count++))
    done
    log "INFO" "端口 $port 已启动"
}

# 检查后端依赖
check_backend_dependencies() {
    log "INFO" "检查后端依赖..."

    # 检查Python
    if ! check_command "python3" "Python3"; then
        return 1
    fi

    # 检查pip
    if ! check_command "pip3" "pip3"; then
        return 1
    fi

    # 检查虚拟环境
    if [ ! -d "$BACKEND_DIR/venv" ]; then
        log "WARN" "未找到虚拟环境，正在创建..."
        cd "$BACKEND_DIR"
        python3 -m venv venv
        log "INFO" "虚拟环境创建完成"
    fi

    # 激活虚拟环境并安装依赖
    log "INFO" "激活虚拟环境并安装依赖..."
    source "$BACKEND_DIR/venv/bin/activate"

    if [ ! -f "$BACKEND_DIR/venv/installed" ]; then
        pip install -r "$BACKEND_DIR/requirements.txt"
        touch "$BACKEND_DIR/venv/installed"
        log "INFO" "后端依赖安装完成"
    else
        log "DEBUG" "后端依赖已安装，跳过安装步骤"
    fi

    deactivate
}

# 检查前端依赖
check_frontend_dependencies() {
    log "INFO" "检查前端依赖..."

    # 检查Node.js
    if ! check_command "node" "Node.js"; then
        return 1
    fi

    # 检查npm
    if ! check_command "npm" "npm"; then
        return 1
    fi

    # 检查并安装依赖
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        log "INFO" "安装前端依赖..."
        npm install
        log "INFO" "前端依赖安装完成"
    else
        log "DEBUG" "前端依赖已存在，跳过安装步骤"
    fi
}

# 检查Docker依赖
check_docker_dependencies() {
    log "INFO" "检查Docker依赖..."

    # 检查Docker
    if ! check_command "docker" "Docker"; then
        return 1
    fi

    # 检查Docker Compose
    if ! check_command "docker-compose" "Docker Compose"; then
        return 1
    fi

    # 检查Docker服务是否运行
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "Docker服务未运行，请启动Docker服务"
        return 1
    fi
}

# 启动后端服务
start_backend() {
    log "INFO" "启动后端服务..."

    # 检查端口，根据FORCE_CLEANUP决定是否强制清理
    if ! check_port $BACKEND_PORT "后端" $FORCE_CLEANUP; then
        if [ "$FORCE_CLEANUP" = true ]; then
            log "ERROR" "无法清理后端端口 $BACKEND_PORT"
        else
            log "ERROR" "后端端口 $BACKEND_PORT 已被占用，使用 --force 选项强制清理"
        fi
        return 1
    fi

    cd "$BACKEND_DIR"

    if [ "$DOCKER_MODE" = true ]; then
        log "INFO" "使用Docker模式启动后端"
        docker-compose up -d api
        echo $! > "$DOCKER_COMPOSE_PID_FILE"
    else
        log "INFO" "使用本地模式启动后端"

        # 激活虚拟环境
        source "venv/bin/activate"

        # 启动后端服务
        nohup python start.py > "$BACKEND_LOG" 2>&1 &
        local backend_pid=$!
        echo $backend_pid > "$BACKEND_PID_FILE"

        deactivate

        log "INFO" "后端服务已启动 (PID: $backend_pid)"
    fi

    # 等待服务启动
    wait_for_port $BACKEND_PORT
}

# 启动前端服务
start_frontend() {
    log "INFO" "启动前端服务..."

    # 检查端口，根据FORCE_CLEANUP决定是否强制清理
    if ! check_port $FRONTEND_PORT "前端" $FORCE_CLEANUP; then
        if [ "$FORCE_CLEANUP" = true ]; then
            log "ERROR" "无法清理前端端口 $FRONTEND_PORT"
        else
            log "ERROR" "前端端口 $FRONTEND_PORT 已被占用，使用 --force 选项强制清理"
        fi
        return 1
    fi

    cd "$FRONTEND_DIR"

    if [ "$DOCKER_MODE" = true ]; then
        log "INFO" "使用Docker模式启动前端"
        # 注意：前端Docker配置可能需要单独处理
        log "WARN" "前端Docker模式暂未配置，使用本地模式"
        DOCKER_MODE=false
    fi

    if [ "$DOCKER_MODE" = false ]; then
        log "INFO" "使用本地模式启动前端"

        # 设置环境变量
        export PORT=$FRONTEND_PORT
        
        # 根据模式设置API基础URL
        if [ "$LAN_MODE" = true ]; then
            local local_ip=$(get_local_ip)
            export REACT_APP_API_BASE_URL="http://$local_ip:$BACKEND_PORT/api/v1"
            log "INFO" "局域网模式：前端将连接到 $local_ip:$BACKEND_PORT"
        else
            export REACT_APP_API_BASE_URL="http://localhost:$BACKEND_PORT/api/v1"
        fi

        # 启动前端服务
        nohup npm start > "$FRONTEND_LOG" 2>&1 &
        local frontend_pid=$!
        echo $frontend_pid > "$FRONTEND_PID_FILE"

        log "INFO" "前端服务已启动 (PID: $frontend_pid)"
    fi

    # 等待服务启动
    wait_for_port $FRONTEND_PORT
}

# 强制停止占用端口的进程
force_kill_port() {
    local port="$1"
    local service_name="$2"
    
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        log "INFO" "发现占用$service_name端口 $port 的进程: $pids"
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                log "INFO" "终止进程 $pid (占用$service_name端口 $port)"
                kill -TERM $pid 2>/dev/null
                sleep 2
                # 如果进程仍然存在，强制杀死
                if kill -0 $pid 2>/dev/null; then
                    log "WARN" "进程 $pid 未响应TERM信号，使用KILL信号"
                    kill -KILL $pid 2>/dev/null
                fi
            fi
        done
        # 再次检查端口是否已释放
        sleep 1
        if lsof -ti :$port >/dev/null 2>&1; then
            log "ERROR" "$service_name端口 $port 仍被占用"
            return 1
        else
            log "INFO" "$service_name端口 $port 已释放"
        fi
    else
        log "DEBUG" "$service_name端口 $port 未被占用"
    fi
    return 0
}

# 停止后端服务
stop_backend() {
    log "INFO" "停止后端服务..."

    if [ "$DOCKER_MODE" = true ]; then
        if [ -f "$DOCKER_COMPOSE_PID_FILE" ]; then
            cd "$BACKEND_DIR"
            docker-compose down
            rm -f "$DOCKER_COMPOSE_PID_FILE"
            log "INFO" "Docker后端服务已停止"
        else
            log "WARN" "未找到Docker后端服务进程"
        fi
    else
        # 首先尝试通过PID文件停止
        if [ -f "$BACKEND_PID_FILE" ]; then
            local backend_pid=$(cat "$BACKEND_PID_FILE")
            if kill -0 $backend_pid 2>/dev/null; then
                log "INFO" "通过PID文件停止后端服务 (PID: $backend_pid)"
                kill -TERM $backend_pid 2>/dev/null
                sleep 2
                # 检查进程是否仍然存在
                if kill -0 $backend_pid 2>/dev/null; then
                    log "WARN" "后端进程未响应TERM信号，使用KILL信号"
                    kill -KILL $backend_pid 2>/dev/null
                fi
            fi
            rm -f "$BACKEND_PID_FILE"
        fi
        
        # 强制清理占用后端端口的所有进程
        force_kill_port $BACKEND_PORT "后端"
    fi
}

# 停止前端服务
stop_frontend() {
    log "INFO" "停止前端服务..."

    # 首先尝试通过PID文件停止
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        if kill -0 $frontend_pid 2>/dev/null; then
            log "INFO" "通过PID文件停止前端服务 (PID: $frontend_pid)"
            kill -TERM $frontend_pid 2>/dev/null
            sleep 2
            # 检查进程是否仍然存在
            if kill -0 $frontend_pid 2>/dev/null; then
                log "WARN" "前端进程未响应TERM信号，使用KILL信号"
                kill -KILL $frontend_pid 2>/dev/null
            fi
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    # 强制清理占用前端端口的所有进程
    force_kill_port $FRONTEND_PORT "前端"
}

# 显示服务状态
show_status() {
    echo -e "${CYAN}=== UDBM 项目状态 ===${NC}"

    # 检查后端状态
    if [ "$DOCKER_MODE" = true ]; then
        if docker ps | grep -q udbm-api; then
            echo -e "${GREEN}后端服务 (Docker):${NC} 运行中"
        else
            echo -e "${RED}后端服务 (Docker):${NC} 未运行"
        fi
    else
        if [ -f "$BACKEND_PID_FILE" ]; then
            local backend_pid=$(cat "$BACKEND_PID_FILE")
            if kill -0 $backend_pid 2>/dev/null; then
                echo -e "${GREEN}后端服务:${NC} 运行中 (PID: $backend_pid)"
            else
                echo -e "${RED}后端服务:${NC} 进程不存在 (PID: $backend_pid)"
            fi
        else
            echo -e "${RED}后端服务:${NC} 未运行"
        fi
    fi

    # 检查前端状态
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        if kill -0 $frontend_pid 2>/dev/null; then
            echo -e "${GREEN}前端服务:${NC} 运行中 (PID: $frontend_pid)"
        else
            echo -e "${RED}前端服务:${NC} 进程不存在 (PID: $frontend_pid)"
        fi
    else
        echo -e "${RED}前端服务:${NC} 未运行"
    fi

    # 检查端口状态
    echo ""
    echo -e "${BLUE}端口状态:${NC}"
    if nc -z localhost $BACKEND_PORT 2>/dev/null; then
        echo -e "  后端端口 $BACKEND_PORT: ${GREEN}开放${NC}"
    else
        echo -e "  后端端口 $BACKEND_PORT: ${RED}关闭${NC}"
    fi

    if nc -z localhost $FRONTEND_PORT 2>/dev/null; then
        echo -e "  前端端口 $FRONTEND_PORT: ${GREEN}开放${NC}"
    else
        echo -e "  前端端口 $FRONTEND_PORT: ${RED}关闭${NC}"
    fi
}

# 显示日志
show_logs() {
    local service="$1"

    case $service in
        "backend"|"b")
            if [ -f "$BACKEND_LOG" ]; then
                echo -e "${CYAN}=== 后端服务日志 ===${NC}"
                tail -f "$BACKEND_LOG"
            else
                log "ERROR" "后端日志文件不存在"
            fi
            ;;
        "frontend"|"f")
            if [ -f "$FRONTEND_LOG" ]; then
                echo -e "${CYAN}=== 前端服务日志 ===${NC}"
                tail -f "$FRONTEND_LOG"
            else
                log "ERROR" "前端日志文件不存在"
            fi
            ;;
        *)
            echo -e "${CYAN}=== 后端服务日志 ===${NC}"
            if [ -f "$BACKEND_LOG" ]; then
                tail -f "$BACKEND_LOG"
            else
                echo "后端日志文件不存在"
            fi

            echo -e "\n${CYAN}=== 前端服务日志 ===${NC}"
            if [ -f "$FRONTEND_LOG" ]; then
                tail -f "$FRONTEND_LOG"
            else
                echo "前端日志文件不存在"
            fi
            ;;
    esac
}

# 清理函数
cleanup() {
    log "INFO" "清理临时文件和容器..."

    # 停止服务
    stop_backend
    stop_frontend

    # 清理Docker容器
    if [ "$DOCKER_MODE" = true ]; then
        cd "$BACKEND_DIR"
        docker-compose down -v
        docker system prune -f
    fi

    # 清理PID文件和日志
    rm -rf "$PID_DIR" "$LOG_DIR"

    log "INFO" "清理完成"
}

# 主函数
main() {
    local command="start"
    local only_backend=false
    local only_frontend=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--docker)
                DOCKER_MODE=true
                shift
                ;;
            -b|--backend)
                only_backend=true
                shift
                ;;
            -f|--frontend)
                only_frontend=true
                shift
                ;;
            -p|--port)
                if [[ $only_backend == true ]]; then
                    BACKEND_PORT="$2"
                elif [[ $only_frontend == true ]]; then
                    FRONTEND_PORT="$2"
                else
                    BACKEND_PORT="$2"
                    FRONTEND_PORT="$((BACKEND_PORT + 1))"
                fi
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -s|--skip)
                SKIP_CHECKS=true
                shift
                ;;
            -l|--lan)
                LAN_MODE=true
                shift
                ;;
            --force)
                FORCE_CLEANUP=true
                shift
                ;;
            start|stop|restart|status|logs|clean)
                command="$1"
                shift
                ;;
            *)
                log "ERROR" "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 创建必要的目录
    create_directories

    # 执行命令
    case $command in
        "start")
            log "INFO" "开始启动 UDBM 项目..."

            # 检查依赖
            if [ "$SKIP_CHECKS" = false ]; then
                if [ "$DOCKER_MODE" = true ]; then
                    check_docker_dependencies || exit 1
                else
                    if [ "$only_backend" = true ] || [ "$only_frontend" = false ]; then
                        check_backend_dependencies || exit 1
                    fi
                    if [ "$only_frontend" = true ] || [ "$only_backend" = false ]; then
                        check_frontend_dependencies || exit 1
                    fi
                fi
            fi

            # 启动服务
            if [ "$only_backend" = false ] && [ "$only_frontend" = false ]; then
                # 启动全部服务
                start_backend || exit 1
                start_frontend || exit 1
            elif [ "$only_backend" = true ]; then
                # 仅启动后端
                start_backend || exit 1
            elif [ "$only_frontend" = true ]; then
                # 仅启动前端
                start_frontend || exit 1
            fi

            log "INFO" "UDBM 项目启动完成!"
            echo ""
            echo -e "${GREEN}访问地址:${NC}"
            
            if [ "$LAN_MODE" = true ]; then
                local local_ip=$(get_local_ip)
                echo -e "  前端: http://localhost:$FRONTEND_PORT (本机)"
                echo -e "  前端: http://$local_ip:$FRONTEND_PORT (局域网)"
                echo -e "  后端API: http://localhost:$BACKEND_PORT (本机)"
                echo -e "  后端API: http://$local_ip:$BACKEND_PORT (局域网)"
                echo -e "  API文档: http://localhost:$BACKEND_PORT/docs (本机)"
                echo -e "  API文档: http://$local_ip:$BACKEND_PORT/docs (局域网)"
                echo ""
                echo -e "${YELLOW}局域网访问说明:${NC}"
                echo -e "  同事可以通过 http://$local_ip:$FRONTEND_PORT 访问前端"
                echo -e "  确保防火墙允许端口 $FRONTEND_PORT 和 $BACKEND_PORT 的访问"
            else
                echo -e "  前端: http://localhost:$FRONTEND_PORT"
                echo -e "  后端API: http://localhost:$BACKEND_PORT"
                echo -e "  API文档: http://localhost:$BACKEND_PORT/docs"
            fi
            ;;
        "stop")
            log "INFO" "停止 UDBM 项目..."
            stop_backend
            stop_frontend
            log "INFO" "UDBM 项目已停止"
            ;;
        "restart")
            log "INFO" "重启 UDBM 项目..."
            stop_backend
            stop_frontend
            sleep 2
            exec "$0" start "$@"
            ;;
        "status")
            show_status
            ;;
        "logs")
            if [ "$only_backend" = true ]; then
                show_logs "backend"
            elif [ "$only_frontend" = true ]; then
                show_logs "frontend"
            else
                show_logs "all"
            fi
            ;;
        "clean")
            cleanup
            ;;
        *)
            log "ERROR" "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'log "WARN" "收到中断信号，正在清理..."; stop_backend; stop_frontend; exit 1' INT TERM

# 执行主函数
main "$@"
