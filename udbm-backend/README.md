# UDBM - 统一数据库管理平台 (后端)

## 项目概述

UDBM (Unified Database Management) 是一个统一数据库管理平台，专为管理全国多个分公司的数据库系统而设计。该平台提供数据库监控、自动化运维、智能巡检等功能。

## 功能特性

### MVP版本功能
- ✅ 数据库实例管理 (注册、更新、删除)
- ✅ PostgreSQL数据库连接测试
- ✅ 基础健康检查API
- ✅ RESTful API设计
- 🔄 用户权限管理 (开发中)
- 🔄 监控指标收集 (开发中)
- 🔄 备份恢复功能 (开发中)

## 技术栈

- **后端框架**: FastAPI
- **数据库ORM**: SQLAlchemy 2.0
- **数据库**: PostgreSQL 15
- **数据验证**: Pydantic
- **缓存**: Redis (可选)
- **容器化**: Docker

## 快速开始

### 1. 环境准备

确保安装了以下软件：
- Python 3.9+
- PostgreSQL 15+
- Docker (可选)

### 2. 安装依赖

```bash
cd udbm-backend
pip install -r requirements.txt
```

### 3. 数据库设置

#### 方式1: 使用Docker (推荐)

```bash
# 启动PostgreSQL和Redis（首次启动将自动执行 init.sql、performance_tuning_tables.sql、sample_performance_data.sql）
docker-compose up -d postgres redis
```

#### 方式2: 本地PostgreSQL

```bash
# 创建数据库
createdb -U postgres udbm_db

# 创建用户
createuser -U postgres udbm_user
psql -U postgres -c "ALTER USER udbm_user PASSWORD 'udbm_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE udbm_db TO udbm_user;"

# 初始化表结构
psql -U udbm_user -d udbm_db -f init.sql
```

### 4. 启动应用

```bash
# 方式1: 启动脚本
python start.py

# 方式2: 直接运行（开发）
uvicorn app.main:app --reload
```

应用将在 http://localhost:8000 启动

### 5. 验证安装

访问以下地址验证安装：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health/
- **数据库列表**: http://localhost:8000/api/v1/databases/

## API接口

### 数据库管理

#### 获取数据库列表
```http
GET /api/v1/databases/
```

#### 创建数据库实例
```http
POST /api/v1/databases/
Content-Type: application/json

{
  "name": "生产数据库",
  "type_id": 1,
  "host": "localhost",
  "port": 5432,
  "database_name": "myapp_prod",
  "username": "myapp_user",
  "password_encrypted": "encrypted_password",
  "environment": "production"
}
```

#### 测试数据库连接
```http
POST /api/v1/databases/{database_id}/test-connection
```

### 健康检查

#### 基础健康检查
```http
GET /api/v1/health/
```

#### 数据库健康检查
```http
GET /api/v1/health/database
```

## 项目结构

```
udbm-backend/
├── app/
│   ├── api/              # API路由
│   │   └── v1/
│   │       ├── endpoints/    # API端点
│   │       └── api.py        # API路由聚合
│   ├── core/             # 核心配置
│   │   └── config.py         # 应用配置
│   ├── db/               # 数据库配置
│   │   ├── base.py           # 数据库基础模型
│   │   ├── session.py        # 数据库会话管理
│   │   └── models/          # 数据模型
│   ├── models/           # SQLAlchemy模型
│   ├── schemas/          # Pydantic模型
│   ├── services/         # 业务服务层
│   ├── utils/            # 工具函数
│   └── main.py           # 应用入口
├── tests/               # 测试文件
├── init.sql            # 数据库初始化脚本
├── requirements.txt    # Python依赖
├── Dockerfile         # Docker镜像配置
├── docker-compose.yml # Docker编排配置
├── start.py           # 启动脚本
└── README.md          # 项目文档
```

## 数据库设计

### 核心表结构

- **users**: 用户信息表
- **roles**: 角色表
- **user_roles**: 用户角色关联表
- **permissions**: 权限表
- **role_permissions**: 角色权限关联表
- **database_types**: 数据库类型表
- **database_instances**: 数据库实例表
- **database_groups**: 数据库分组表
- **database_group_members**: 分组成员表
- **metric_definitions**: 监控指标定义表
- **metrics**: 监控指标数据表
- **alert_rules**: 告警规则表
- **alerts**: 告警历史表

## 开发指南

### 添加新API端点

1. 在 `app/api/v1/endpoints/` 下创建新文件
2. 实现FastAPI路由
3. 在 `app/api/v1/api.py` 中注册路由
4. 添加相应的Pydantic模型到 `app/schemas/`

### 数据库迁移

当前版本使用SQL脚本来管理数据库结构。在生产环境中，建议使用Alembic进行数据库迁移管理。

### 测试

```bash
# 运行测试
pytest tests/

# 带覆盖率测试
pytest --cov=app tests/
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t udbm-backend .

# 运行容器
docker run --env POSTGRES_SERVER=postgres \
           --env POSTGRES_USER=udbm_user \
           --env POSTGRES_PASSWORD=udbm_password \
           --env POSTGRES_DB=udbm_db \
           -p 8000:8000 udbm-backend
```

### Docker Compose部署

```bash
# 启动所有服务（postgres、redis、api、可选pgadmin）
docker-compose up -d

# 查看日志
docker-compose logs -f api

## 健康检查

- 基础健康检查: `GET /health` 或 `GET /api/v1/health/`
- 数据库健康检查: `GET /api/v1/health/database`
- 详细健康检查: `GET /api/v1/health/detailed`
```

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

项目维护者: [您的姓名]

项目主页: [项目地址]
