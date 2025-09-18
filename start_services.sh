#!/bin/bash

# UDBM服务启动脚本
# 用于启动所有必要的服务并监控状态

echo "=== UDBM服务启动脚本 ==="
echo "时间: $(date)"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行，请先启动Docker"
    exit 1
fi

# 启动PostgreSQL容器
echo "启动PostgreSQL容器..."
docker start udbm-postgres > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL容器已启动"
else
    echo "✗ PostgreSQL容器启动失败"
    exit 1
fi

# 等待PostgreSQL启动
echo "等待PostgreSQL启动..."
sleep 5

# 检查PostgreSQL是否可用
for i in {1..10}; do
    if docker exec udbm-postgres pg_isready -U udbm_user -d udbm_db > /dev/null 2>&1; then
        echo "✓ PostgreSQL已就绪"
        break
    fi
    echo "等待PostgreSQL启动... ($i/10)"
    sleep 2
done

# 启动后端服务
echo "启动后端服务..."
cd /Users/isadmin/StudyCursor/UDBM/udbm-backend
if [ -f "start.py" ]; then
    # 杀死现有进程
    pkill -f "python.*start.py" 2>/dev/null
    sleep 2
    
    # 启动新进程
    nohup python start.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "✓ 后端服务已启动 (PID: $BACKEND_PID)"
else
    echo "✗ 找不到后端启动文件"
    exit 1
fi

# 等待后端服务启动
echo "等待后端服务启动..."
sleep 5

# 检查后端服务是否可用
for i in {1..10}; do
    if curl -s http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
        echo "✓ 后端服务已就绪"
        break
    fi
    echo "等待后端服务启动... ($i/10)"
    sleep 2
done

# 检查前端服务
echo "检查前端服务..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ 前端服务运行正常"
else
    echo "⚠ 前端服务未运行，请手动启动: cd udbm-frontend && npm start"
fi

# 显示服务状态
echo ""
echo "=== 服务状态 ==="
echo "PostgreSQL: http://localhost:5432"
echo "后端API: http://localhost:8000"
echo "前端界面: http://localhost:3000"
echo ""
echo "监控日志: tail -f logs/backend.log"
echo "数据库监控: python monitor_db_connections.py"
echo ""
echo "所有服务已启动完成！"
