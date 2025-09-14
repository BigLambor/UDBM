#!/bin/bash

# UDBM MySQL 测试环境启动脚本
# 用于启动MySQL容器并创建测试数据库实例

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/udbm-backend"

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
        *)
            echo -e "${CYAN}[$timestamp] $level:${NC} $message"
            ;;
    esac
}

# 检查Docker是否运行
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "Docker服务未运行，请启动Docker服务"
        return 1
    fi
    log "INFO" "Docker服务运行正常"
}

# 检查端口是否可用
check_port() {
    local port="$1"
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log "WARN" "端口 $port 已被占用"
        return 1
    fi
    log "INFO" "端口 $port 可用"
}

# 等待端口启动
wait_for_port() {
    local port="$1"
    local timeout="${2:-60}"
    local count=0

    log "INFO" "等待端口 $port 启动..."
    while ! nc -z localhost $port 2>/dev/null; do
        if [ $count -ge $timeout ]; then
            log "ERROR" "端口 $port 启动超时"
            return 1
        fi
        sleep 1
        ((count++))
        if [ $((count % 10)) -eq 0 ]; then
            log "INFO" "等待中... ($count/$timeout 秒)"
        fi
    done
    log "INFO" "端口 $port 已启动"
}

# 启动MySQL容器
start_mysql() {
    log "INFO" "启动MySQL容器..."
    
    cd "$BACKEND_DIR"
    
    # 只启动MySQL服务
    docker-compose up -d mysql
    
    if [ $? -eq 0 ]; then
        log "INFO" "MySQL容器启动成功"
        
        # 等待MySQL服务启动
        wait_for_port 3306 60
        
        # 等待额外时间让MySQL完全初始化
        log "INFO" "等待MySQL初始化完成..."
        sleep 10
        
        return 0
    else
        log "ERROR" "MySQL容器启动失败"
        return 1
    fi
}

# 测试MySQL连接
test_mysql_connection() {
    log "INFO" "测试MySQL连接..."
    
    # 使用docker exec测试连接
    if docker exec udbm-mysql mysql -u udbm_mysql_user -pudbm_mysql_password -e "SELECT 'MySQL连接成功!' as status;" 2>/dev/null; then
        log "INFO" "✅ MySQL连接测试成功"
        return 0
    else
        log "ERROR" "❌ MySQL连接测试失败"
        return 1
    fi
}

# 显示MySQL信息
show_mysql_info() {
    log "INFO" "获取MySQL服务信息..."
    
    echo -e "${CYAN}=== MySQL容器信息 ===${NC}"
    docker ps --filter "name=udbm-mysql" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${CYAN}=== MySQL连接信息 ===${NC}"
    echo -e "主机: ${GREEN}localhost${NC}"
    echo -e "端口: ${GREEN}3306${NC}"
    echo -e "数据库: ${GREEN}udbm_mysql_demo${NC}"
    echo -e "用户名: ${GREEN}udbm_mysql_user${NC}"
    echo -e "密码: ${GREEN}udbm_mysql_password${NC}"
    
    echo -e "\n${CYAN}=== 数据库统计信息 ===${NC}"
    docker exec udbm-mysql mysql -u udbm_mysql_user -pudbm_mysql_password udbm_mysql_demo -e "
        SELECT 'users' as table_name, COUNT(*) as record_count FROM users
        UNION ALL
        SELECT 'categories', COUNT(*) FROM categories
        UNION ALL
        SELECT 'products', COUNT(*) FROM products
        UNION ALL
        SELECT 'orders', COUNT(*) FROM orders
        UNION ALL
        SELECT 'order_items', COUNT(*) FROM order_items
        UNION ALL
        SELECT 'activity_logs', COUNT(*) FROM activity_logs
        UNION ALL
        SELECT 'performance_test', COUNT(*) FROM performance_test;
    " 2>/dev/null || log "WARN" "无法获取数据库统计信息（可能数据还在初始化中）"
}

# 停止MySQL容器
stop_mysql() {
    log "INFO" "停止MySQL容器..."
    
    cd "$BACKEND_DIR"
    docker-compose stop mysql
    
    log "INFO" "MySQL容器已停止"
}

# 清理MySQL容器和数据
cleanup_mysql() {
    log "INFO" "清理MySQL容器和数据..."
    
    cd "$BACKEND_DIR"
    docker-compose down mysql
    docker volume rm udbm-backend_mysql_data 2>/dev/null || true
    
    log "INFO" "MySQL环境清理完成"
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}UDBM MySQL 测试环境管理脚本${NC}"
    echo -e "${BLUE}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${BLUE}命令:${NC}"
    echo "  start       启动MySQL测试环境 (默认)"
    echo "  stop        停止MySQL容器"
    echo "  restart     重启MySQL容器"
    echo "  status      查看MySQL状态"
    echo "  test        测试MySQL连接"
    echo "  info        显示MySQL连接信息"
    echo "  logs        查看MySQL日志"
    echo "  cleanup     清理MySQL容器和数据"
    echo "  help        显示帮助信息"
    echo ""
    echo -e "${BLUE}示例:${NC}"
    echo "  $0 start       # 启动MySQL测试环境"
    echo "  $0 test        # 测试MySQL连接"
    echo "  $0 info        # 显示连接信息和数据统计"
    echo "  $0 cleanup     # 完全清理MySQL环境"
}

# 主函数
main() {
    local command="${1:-start}"
    
    case $command in
        "start")
            log "INFO" "开始启动MySQL测试环境..."
            
            # 检查Docker
            check_docker || exit 1
            
            # 启动MySQL
            if start_mysql; then
                # 测试连接
                sleep 5  # 给MySQL更多时间初始化
                if test_mysql_connection; then
                    log "INFO" "✅ MySQL测试环境启动成功！"
                    echo ""
                    show_mysql_info
                    echo ""
                    echo -e "${GREEN}MySQL测试环境已就绪，可以在UDBM系统中添加此数据库实例进行测试${NC}"
                else
                    log "WARN" "MySQL容器已启动，但连接测试失败，可能还在初始化中"
                    log "INFO" "请稍等片刻后使用 '$0 test' 命令重新测试"
                fi
            else
                log "ERROR" "MySQL测试环境启动失败"
                exit 1
            fi
            ;;
        "stop")
            stop_mysql
            ;;
        "restart")
            log "INFO" "重启MySQL容器..."
            stop_mysql
            sleep 2
            exec "$0" start
            ;;
        "status")
            echo -e "${CYAN}=== MySQL容器状态 ===${NC}"
            if docker ps --filter "name=udbm-mysql" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q udbm-mysql; then
                docker ps --filter "name=udbm-mysql" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
                echo -e "\n${GREEN}MySQL容器正在运行${NC}"
                
                if nc -z localhost 3306 2>/dev/null; then
                    echo -e "端口3306: ${GREEN}可访问${NC}"
                else
                    echo -e "端口3306: ${RED}不可访问${NC}"
                fi
            else
                echo -e "${RED}MySQL容器未运行${NC}"
            fi
            ;;
        "test")
            test_mysql_connection
            ;;
        "info")
            show_mysql_info
            ;;
        "logs")
            log "INFO" "显示MySQL容器日志..."
            docker logs -f udbm-mysql
            ;;
        "cleanup")
            read -p "确定要清理所有MySQL数据吗？这将删除所有测试数据 (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                cleanup_mysql
            else
                log "INFO" "取消清理操作"
            fi
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log "ERROR" "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
