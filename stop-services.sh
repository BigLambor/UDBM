#!/bin/bash

# UDBM 服务停止脚本

echo "🛑 停止UDBM服务..."

# 停止前端服务 (端口3000)
echo "停止前端服务..."
FRONTEND_PID=$(lsof -ti:3000)
if [ ! -z "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID
    echo "✅ 前端服务已停止 (PID: $FRONTEND_PID)"
else
    echo "ℹ️  前端服务未运行"
fi

# 停止后端服务 (端口8000)
echo "停止后端服务..."
BACKEND_PID=$(lsof -ti:8000)
if [ ! -z "$BACKEND_PID" ]; then
    kill $BACKEND_PID
    echo "✅ 后端服务已停止 (PID: $BACKEND_PID)"
else
    echo "ℹ️  后端服务未运行"
fi

# 停止MySQL服务 (如果正在运行)
echo "停止MySQL服务..."
if pgrep -x "mysqld" > /dev/null; then
    sudo brew services stop mysql
    echo "✅ MySQL服务已停止"
else
    echo "ℹ️  MySQL服务未运行"
fi

# 停止PostgreSQL服务 (如果正在运行)
echo "停止PostgreSQL服务..."
if pgrep -x "postgres" > /dev/null; then
    brew services stop postgresql
    echo "✅ PostgreSQL服务已停止"
else
    echo "ℹ️  PostgreSQL服务未运行"
fi

echo ""
echo "🎉 所有服务已停止!"
