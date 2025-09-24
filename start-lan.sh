#!/bin/bash

# UDBM 局域网启动脚本
# 专门用于启动局域网可访问的服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# 检查端口是否被占用
check_port() {
    local port="$1"
    local name="$2"
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}警告: $name 端口 $port 已被占用${NC}"
        return 1
    fi
    return 0
}

# 强制清理端口
force_kill_port() {
    local port="$1"
    local service_name="$2"
    
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}发现占用$service_name端口 $port 的进程: $pids${NC}"
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}终止进程 $pid (占用$service_name端口 $port)${NC}"
                kill -TERM $pid 2>/dev/null
                sleep 2
                if kill -0 $pid 2>/dev/null; then
                    kill -KILL $pid 2>/dev/null
                fi
            fi
        done
        sleep 1
        if lsof -ti :$port >/dev/null 2>&1; then
            echo -e "${RED}错误: $service_name端口 $port 仍被占用${NC}"
            return 1
        else
            echo -e "${GREEN}$service_name端口 $port 已释放${NC}"
        fi
    fi
    return 0
}

# 显示网络信息
show_network_info() {
    local local_ip=$(get_local_ip)
    
    echo -e "${CYAN}=== 网络信息 ===${NC}"
    echo -e "本机IP地址: ${GREEN}$local_ip${NC}"
    echo -e "前端端口: ${GREEN}3000${NC}"
    echo -e "后端端口: ${GREEN}8000${NC}"
    echo ""
    echo -e "${CYAN}=== 访问地址 ===${NC}"
    echo -e "本机访问:"
    echo -e "  前端: ${GREEN}http://localhost:3000${NC}"
    echo -e "  后端API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  API文档: ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "局域网访问:"
    echo -e "  前端: ${GREEN}http://$local_ip:3000${NC}"
    echo -e "  后端API: ${GREEN}http://$local_ip:8000${NC}"
    echo -e "  API文档: ${GREEN}http://$local_ip:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}同事访问说明:${NC}"
    echo -e "1. 确保同事与您在同一局域网内"
    echo -e "2. 同事可以通过 http://$local_ip:3000 访问前端"
    echo -e "3. 确保防火墙允许端口 3000 和 8000 的访问"
    echo -e "4. 如果无法访问，请检查防火墙设置"
}

# 检查防火墙状态（macOS）
check_firewall_macos() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local firewall_status=$(sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep "Firewall is enabled" || echo "disabled")
        if [[ "$firewall_status" == *"enabled"* ]]; then
            echo -e "${YELLOW}检测到macOS防火墙已启用${NC}"
            echo -e "${YELLOW}如果同事无法访问，请执行以下命令允许端口访问:${NC}"
            echo -e "sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3"
            echo -e "sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/node"
        fi
    fi
}

# 主函数
main() {
    echo -e "${CYAN}UDBM 局域网启动脚本${NC}"
    echo -e "${BLUE}此脚本将启动UDBM服务，允许局域网内的同事访问${NC}"
    echo ""
    
    # 显示网络信息
    show_network_info
    echo ""
    
    # 检查防火墙
    check_firewall_macos
    echo ""
    
    # 检查端口
    if ! check_port 8000 "后端"; then
        echo -e "${YELLOW}是否强制清理后端端口? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            force_kill_port 8000 "后端" || exit 1
        else
            echo -e "${RED}无法启动，端口被占用${NC}"
            exit 1
        fi
    fi
    
    if ! check_port 3000 "前端"; then
        echo -e "${YELLOW}是否强制清理前端端口? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            force_kill_port 3000 "前端" || exit 1
        else
            echo -e "${RED}无法启动，端口被占用${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}端口检查通过，开始启动服务...${NC}"
    echo ""
    
    # 调用主启动脚本，使用局域网模式
    exec "$(dirname "$0")/start-project.sh" start --lan --force
}

# 执行主函数
main "$@"
