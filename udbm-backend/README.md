# UDBM - 统一数据库管理平台 (后端)

## 项目概述

UDBM (Unified Database Management) 后端是基于FastAPI构建的现代化数据库管理API服务，为统一数据库管理平台提供强大的后端支持。支持多种数据库类型的管理、监控、性能调优等功能。

## 功能特性

### 🚀 核心功能
- ✅ **多数据库支持**: PostgreSQL、MySQL、MongoDB、Redis
- ✅ **数据库实例管理**: 注册、更新、删除、连接测试
- ✅ **连接池管理**: 智能连接池配置和监控
- ✅ **健康检查**: 多层级健康状态监控
- ✅ **RESTful API**: 完整的REST API设计

### 🔧 性能调优功能
- ✅ **慢查询分析**: 自动识别和分析慢查询
- ✅ **执行计划分析**: SQL执行计划解析和优化建议
- ✅ **索引优化**: 缺失索引检测和优化建议
- ✅ **系统诊断**: 数据库性能指标监控
- ✅ **配置优化**: 数据库参数优化建议
- ✅ **性能基线**: 建立和维护性能基线数据

### 🔄 开发中功能
- 🔄 用户权限管理 (RBAC)
- 🔄 智能告警系统
- 🔄 自动化备份恢复
- 🔄 数据库迁移工具
- 🔄 集群管理功能

## 技术栈

- **Web框架**: FastAPI 0.104+
- **数据库ORM**: SQLAlchemy 2.0 (异步)
- **数据库驱动**: 
  - PostgreSQL: asyncpg, psycopg2
  - MySQL: aiomysql, pymysql
- **数据验证**: Pydantic v2
- **安全认证**: python-jose, passlib
- **异步支持**: asyncio, uvicorn
- **监控**: prometheus-client
- **日志**: structlog
- **容器化**: Docker, Docker Compose

## 项目结构

```
udbm-backend/
├── app/
│   ├── api/                    # API路由层
│   │   └── v1/
│   │       ├── api.py          # 路由聚合
│   │       └── endpoints/      # API端点实现
│   │           ├── databases.py           # 数据库管理API
│   │           ├── performance_tuning.py  # 性能调优API
│   │           └── health.py             # 健康检查API
│   ├── core/                   # 核心配置
│   │   └── config.py           # 应用配置
│   ├── db/                     # 数据库层
│   │   ├── base.py            # 基础模型
│   │   ├── session.py         # 数据库会话管理
│   │   └── init_database_instances.py  # 数据库初始化
│   ├── models/                 # SQLAlchemy模型
│   │   ├── database.py        # 数据库实例模型
│   │   ├── monitoring.py      # 监控相关模型
│   │   └── performance_tuning.py  # 性能调优模型
│   ├── schemas/                # Pydantic数据验证模型
│   │   ├── database.py        # 数据库相关Schema
│   │   └── performance_tuning.py  # 性能调优Schema
│   ├── services/               # 业务服务层
│   │   ├── database_connection.py     # 数据库连接服务
│   │   ├── db_providers/              # 数据库适配器
│   │   │   ├── base.py               # 基础适配器
│   │   │   ├── postgres.py           # PostgreSQL适配器
│   │   │   ├── mysql.py              # MySQL适配器
│   │   │   └── registry.py           # 适配器注册表
│   │   └── performance_tuning/        # 性能调优服务
│   │       ├── slow_query_analyzer.py      # 慢查询分析器
│   │       ├── execution_plan_analyzer.py  # 执行计划分析器
│   │       ├── system_monitor.py          # 系统监控器
│   │       ├── postgres_config_optimizer.py  # PostgreSQL配置优化
│   │       ├── mysql_config_optimizer.py     # MySQL配置优化
│   │       └── tuning_executor.py           # 调优执行器
│   └── main.py                 # 应用入口
├── tests/                      # 测试文件
├── init.sql                    # 基础数据库结构
├── performance_tuning_tables.sql  # 性能调优相关表
├── sample_performance_data.sql    # 示例性能数据
├── requirements.txt            # Python依赖
├── Dockerfile                  # Docker镜像配置
├── docker-compose.yml          # Docker编排配置
├── start.py                    # 启动脚本
└── README.md                   # 项目文档
```

## 快速开始

### 1. 环境准备

确保安装了以下软件：
- Python 3.9+
- PostgreSQL 15+ (推荐)
- Redis 7+ (可选，用于缓存)
- Docker & Docker Compose (推荐)

### 2. 安装依赖

```bash
cd udbm-backend

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库设置

#### 方式1: 使用Docker (推荐)

```bash
# 启动PostgreSQL和Redis
docker-compose up -d postgres redis

# 等待数据库启动
sleep 10

# 初始化数据库结构
docker exec -i udbm-postgres psql -U udbm_user -d udbm_db < init.sql
docker exec -i udbm-postgres psql -U udbm_user -d udbm_db < performance_tuning_tables.sql

# 可选：导入示例数据
docker exec -i udbm-postgres psql -U udbm_user -d udbm_db < sample_performance_data.sql
```

#### 方式2: 本地PostgreSQL

```bash
# 创建数据库和用户
createdb -U postgres udbm_db
createuser -U postgres udbm_user
psql -U postgres -c "ALTER USER udbm_user PASSWORD 'udbm_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE udbm_db TO udbm_user;"

# 初始化表结构
psql -U udbm_user -d udbm_db -f init.sql
psql -U udbm_user -d udbm_db -f performance_tuning_tables.sql

# 可选：导入示例数据
psql -U udbm_user -d udbm_db -f sample_performance_data.sql
```

### 4. 启动应用

```bash
# 方式1: 使用启动脚本 (推荐)
python start.py

# 方式2: 直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式3: 使用Docker
docker-compose up -d api
```

应用将在 http://localhost:8000 启动

### 5. 验证安装

访问以下地址验证安装：

- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/v1/health/
- **详细健康检查**: http://localhost:8000/api/v1/health/detailed

## API接口文档

### 数据库管理API

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
  "environment": "production",
  "description": "生产环境主数据库"
}
```

#### 测试数据库连接
```http
POST /api/v1/databases/{database_id}/test-connection
```

### 性能调优API

#### 获取慢查询分析
```http
GET /api/v1/performance/slow-queries/{database_id}
```

#### 分析SQL查询
```http
POST /api/v1/performance/analyze-query/{database_id}
Content-Type: application/json

{
  "query": "SELECT * FROM users WHERE created_at > '2024-01-01'"
}
```

#### 获取执行计划
```http
POST /api/v1/performance/execution-plan/{database_id}
Content-Type: application/json

{
  "query": "SELECT u.*, p.name FROM users u JOIN profiles p ON u.id = p.user_id"
}
```

#### 获取系统指标
```http
GET /api/v1/performance/system-metrics/{database_id}
```

#### 获取索引优化建议
```http
GET /api/v1/performance/index-recommendations/{database_id}
```

#### 优化数据库配置
```http
POST /api/v1/performance/optimize-config/{database_id}
```

### 健康检查API

#### 基础健康检查
```http
GET /api/v1/health/
```

#### 数据库健康检查
```http
GET /api/v1/health/database
```

#### 详细健康检查
```http
GET /api/v1/health/detailed
```

## 数据库设计

### 核心表结构

#### 用户和权限表
- **users**: 用户信息表
- **roles**: 角色表
- **user_roles**: 用户角色关联表
- **permissions**: 权限表
- **role_permissions**: 角色权限关联表

#### 数据库管理表
- **database_types**: 数据库类型表
- **database_instances**: 数据库实例表
- **database_groups**: 数据库分组表
- **database_group_members**: 分组成员表

#### 监控和指标表
- **metric_definitions**: 监控指标定义表
- **metrics**: 监控指标数据表
- **alert_rules**: 告警规则表
- **alerts**: 告警历史表

#### 性能调优表
- **slow_queries**: 慢查询记录表
- **query_analysis_results**: 查询分析结果表
- **execution_plans**: 执行计划表
- **index_recommendations**: 索引推荐表
- **optimization_suggestions**: 优化建议表
- **performance_baselines**: 性能基线表
- **system_diagnostics**: 系统诊断表
- **config_optimizations**: 配置优化记录表

## 开发指南

### 添加新的数据库类型支持

1. **创建数据库适配器**
   
   在 `app/services/db_providers/` 下创建新文件，例如 `mongodb.py`:

   ```python
   from .base import BaseDBProvider
   
   class MongoDBProvider(BaseDBProvider):
       def __init__(self):
           super().__init__("mongodb")
       
       async def test_connection(self, connection_info: dict) -> bool:
           # 实现MongoDB连接测试逻辑
           pass
       
       async def get_slow_queries(self, connection_info: dict):
           # 实现慢查询获取逻辑
           pass
   ```

2. **注册新的适配器**
   
   在 `app/services/db_providers/registry.py` 中注册:

   ```python
   from .mongodb import MongoDBProvider
   
   # 注册适配器
   register_provider(MongoDBProvider())
   ```

3. **添加数据库类型**
   
   在数据库中添加新的数据库类型记录。

### 添加新的API端点

1. **在 `app/api/v1/endpoints/` 下创建新文件**
2. **实现FastAPI路由**
3. **在 `app/api/v1/api.py` 中注册路由**
4. **添加相应的Pydantic模型到 `app/schemas/`**

示例：

```python
# app/api/v1/endpoints/backup.py
from fastapi import APIRouter, Depends
from app.schemas.backup import BackupCreate, BackupResponse

router = APIRouter()

@router.post("/", response_model=BackupResponse)
async def create_backup(backup: BackupCreate):
    # 实现备份逻辑
    pass
```

### 数据库迁移

当前版本使用SQL脚本管理数据库结构。推荐在生产环境中使用Alembic：

```bash
# 安装Alembic
pip install alembic

# 初始化Alembic
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Add new table"

# 执行迁移
alembic upgrade head
```

### 性能调优服务扩展

添加新的性能调优功能：

1. **在 `app/services/performance_tuning/` 下创建新的分析器**
2. **继承适当的基类**
3. **实现分析逻辑**
4. **在调优执行器中注册**

示例：

```python
# app/services/performance_tuning/connection_analyzer.py
class ConnectionAnalyzer:
    async def analyze_connections(self, db_info: dict):
        # 分析数据库连接情况
        pass
    
    async def get_recommendations(self):
        # 提供连接优化建议
        pass
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_databases.py

# 带覆盖率测试
pytest --cov=app tests/

# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html tests/
```

### 测试数据库

测试使用独立的测试数据库：

```python
# tests/conftest.py
@pytest.fixture
async def test_db():
    # 创建测试数据库连接
    pass
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t udbm-backend:latest .

# 运行容器
docker run -p 8000:8000 -e DATABASE_URL="postgresql://..." udbm-backend:latest
```

### Docker Compose部署

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

### 生产环境配置

1. **环境变量配置**
   
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
   export REDIS_URL="redis://host:6379/0"
   export SECRET_KEY="your-secret-key"
   export ENVIRONMENT="production"
   ```

2. **使用HTTPS**
   
   配置反向代理 (Nginx) 或使用 `uvicorn --ssl-keyfile --ssl-certfile`

3. **日志配置**
   
   配置结构化日志和日志轮转

## 监控和调试

### 应用监控

```bash
# 健康检查
curl http://localhost:8000/api/v1/health/

# 详细健康检查
curl http://localhost:8000/api/v1/health/detailed

# Prometheus指标
curl http://localhost:8000/metrics
```

### 日志监控

```bash
# 查看应用日志
docker-compose logs -f api

# 查看数据库日志
docker-compose logs -f postgres

# 实时监控日志
tail -f logs/app.log
```

### 性能监控

- 使用 Prometheus + Grafana 监控应用指标
- 使用 APM 工具 (如 New Relic, DataDog) 监控应用性能
- 配置数据库监控工具监控数据库性能

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   docker-compose ps postgres
   
   # 检查连接参数
   psql -h localhost -U udbm_user -d udbm_db
   ```

2. **依赖安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip
   
   # 清理缓存
   pip cache purge
   ```

3. **性能问题**
   ```bash
   # 检查数据库连接池
   curl http://localhost:8000/api/v1/health/detailed
   
   # 查看慢查询日志
   docker exec udbm-postgres tail -f /var/log/postgresql/postgresql.log
   ```

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 使用 Black 格式化代码
- 使用 isort 排序导入
- 遵循 PEP 8 规范
- 编写完整的文档字符串
- 添加适当的类型注解

```bash
# 格式化代码
black app/
isort app/

# 检查代码质量
flake8 app/
mypy app/
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 更新日志

### v1.2.0 (2024-12)
- 添加性能调优功能模块
- 支持慢查询分析和优化建议
- 添加执行计划分析功能
- 实现系统诊断和监控
- 支持数据库配置优化

### v1.1.0 (2024-11)
- 添加多数据库支持 (MySQL, MongoDB, Redis)
- 改进连接池管理
- 增强健康检查功能
- 优化API响应性能

### v1.0.0 (2024-10)
- 初始版本发布
- 基础数据库管理功能
- PostgreSQL支持
- RESTful API实现

---

*最后更新: 2024年*