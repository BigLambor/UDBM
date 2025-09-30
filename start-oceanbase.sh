#!/bin/bash

# UDBM OceanBase 启动脚本
# 使用真正的OceanBase社区版Docker镜像

echo "🚀 启动UDBM项目 - 使用真正的OceanBase数据库..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 拉取OceanBase镜像
echo "📥 拉取OceanBase社区版镜像..."
docker pull oceanbase/oceanbase-ce:latest

# 停止并删除已存在的容器
echo "🧹 清理已存在的容器..."
docker-compose -f udbm-backend/docker-compose.yml down

# 启动OceanBase服务
echo "🐳 启动OceanBase数据库..."
cd udbm-backend

# 只启动OceanBase服务
docker-compose up -d oceanbase

# 等待OceanBase启动
echo "⏳ 等待OceanBase启动完成..."
sleep 30

# 检查OceanBase是否启动成功
echo "🔍 检查OceanBase状态..."
if docker exec udbm-oceanbase obclient -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password -e "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ OceanBase启动成功！"
    
    # 初始化数据库
    echo "📊 初始化数据库..."
    docker exec -i udbm-oceanbase obclient -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password < init_oceanbase_real.sql
    
    echo "🎉 OceanBase数据库初始化完成！"
    echo ""
    echo "📋 连接信息："
    echo "   主机: localhost"
    echo "   端口: 2881"
    echo "   用户名: root@test"
    echo "   密码: udbm_ob_root_password"
    echo "   数据库: udbm_oceanbase_demo"
    echo ""
    echo "🔗 连接命令："
    echo "   mysql -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password"
    echo ""
    echo "🌐 或者使用obclient："
    echo "   docker exec -it udbm-oceanbase obclient -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password"
    
else
    echo "❌ OceanBase启动失败，请检查日志："
    docker logs udbm-oceanbase
    exit 1
fi

# 启动其他服务
echo "🚀 启动其他服务..."
docker-compose up -d

echo "✅ 所有服务启动完成！"
echo ""
echo "📊 服务状态："
docker-compose ps
