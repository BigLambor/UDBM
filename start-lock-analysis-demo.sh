#!/bin/bash

# UDBM 锁分析功能演示启动脚本

echo "🔒 UDBM 数据库锁分析功能演示"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装Node.js"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装，请先安装npm"
    exit 1
fi

echo "✅ 环境检查通过"

# 设置工作目录
cd "$(dirname "$0")"

# 1. 启动后端服务
echo ""
echo "🚀 启动后端服务..."
cd udbm-backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 检查数据库连接
echo "🔍 检查数据库连接..."
python -c "
import sys
try:
    from app.db.session import get_db
    from app.db.init_database_instances import init_database_instances
    print('✅ 数据库连接正常')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 数据库连接失败，请检查数据库配置"
    exit 1
fi

# 创建锁分析表
echo "📊 创建锁分析相关表..."
python -c "
import psycopg2
from app.core.config import settings

try:
    # 读取SQL文件
    with open('create_lock_analysis_tables.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 连接数据库
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='udbm',
        user='udbm_user',
        password='udbm_password'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # 执行SQL
    cursor.execute(sql_content)
    print('✅ 锁分析表创建成功')
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ 创建锁分析表失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 创建锁分析表失败"
    exit 1
fi

# 启动后端服务
echo "🚀 启动后端API服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 等待后端服务启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 检查后端服务是否启动成功
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ 后端服务启动成功 (PID: $BACKEND_PID)"

# 2. 启动前端服务
echo ""
echo "🌐 启动前端服务..."
cd ../udbm-frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端服务
echo "🚀 启动前端开发服务器..."
npm start &
FRONTEND_PID=$!

# 等待前端服务启动
echo "⏳ 等待前端服务启动..."
sleep 10

# 检查前端服务是否启动成功
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ 前端服务启动失败"
    kill $FRONTEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ 前端服务启动成功 (PID: $FRONTEND_PID)"

# 3. 运行测试
echo ""
echo "🧪 运行锁分析功能测试..."
cd ..
python3 test_lock_analysis.py

# 4. 显示访问信息
echo ""
echo "🎉 锁分析功能演示环境启动完成!"
echo "=================================="
echo "📊 后端API服务: http://localhost:8000"
echo "🌐 前端界面: http://localhost:3000"
echo "🔒 锁分析页面: http://localhost:3000/performance/lock-analysis"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "🔧 功能特性:"
echo "  - 实时锁监控和分析"
echo "  - 历史锁事件分析"
echo "  - 锁等待链检测"
echo "  - 锁竞争分析"
echo "  - 智能优化建议"
echo "  - 优化脚本生成"
echo "  - 分析报告生成"
echo ""
echo "🛑 停止服务: 按 Ctrl+C 或运行 ./stop-services.sh"
echo ""

# 等待用户中断
trap 'echo ""; echo "🛑 正在停止服务..."; kill $FRONTEND_PID 2>/dev/null; kill $BACKEND_PID 2>/dev/null; echo "✅ 服务已停止"; exit 0' INT

# 保持脚本运行
wait
