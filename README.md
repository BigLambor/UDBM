# UDBM - 统一数据库管理平台 MVP

## 🚀 项目概述

UDBM (Unified Database Management) 是一个统一数据库管理平台，专为管理全国多个分公司的数据库系统而设计。该平台提供数据库监控、自动化运维、智能巡检等功能。

**我们正在干一件疯狂的事情！** - 用AI驱动的方式快速实现一个功能完整的数据库管理平台MVP。

## 🎯 MVP版本特性

### ✅ 已实现功能
- **后端API**: 基于FastAPI的RESTful API服务
- **数据库管理**: PostgreSQL数据库实例的完整CRUD操作
- **连接测试**: 实时测试数据库连接状态
- **前端界面**: 基于React + Ant Design的现代化Web界面
- **数据库建模**: 完整的数据库表结构和关系设计
- **API文档**: 自动生成的Swagger UI文档

### 🔄 待实现功能
- 用户权限管理 (JWT认证、角色权限)
- PostgreSQL监控功能 (性能指标、健康检查)
- 备份恢复功能 (自动化备份、数据恢复)
- 告警系统 (智能告警、通知机制)
- 巡检功能 (自动化巡检、报告生成)

## 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   后端API       │    │   数据库        │
│                 │    │                 │    │                 │
│  React 18       │◄──►│  FastAPI        │◄──►│  PostgreSQL     │
│  Ant Design 5   │    │  SQLAlchemy     │    │  Redis          │
│  Axios          │    │  Pydantic       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 项目结构

```
UDBM/
├── udbm-backend/           # 后端服务
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── db/            # 数据库配置
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # 数据验证
│   │   ├── services/      # 业务服务
│   │   └── main.py        # 应用入口
│   ├── init.sql           # 数据库初始化
│   ├── requirements.txt   # Python依赖
│   ├── Dockerfile         # 容器配置
│   └── README.md          # 后端文档
├── udbm-frontend/         # 前端界面
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API服务
│   │   └── App.js         # 主应用
│   ├── package.json       # 前端依赖
│   ├── Dockerfile         # 容器配置
│   └── README.md          # 前端文档
└── README.md              # 项目总览
```

## 🚀 快速开始

### 1. 一键启动（推荐）

```bash
chmod +x ./start-project.sh
./start-project.sh start         # 本地模式：后端 + 前端

# 常用：仅后端/仅前端/指定端口
./start-project.sh start --backend
./start-project.sh start --frontend
./start-project.sh start --port 8000
```

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 2. 分步启动

方式A：Docker 启动数据库与缓存 + 本地启动后端

```bash
cd udbm-backend
docker-compose up -d postgres redis   # 首次启动将自动执行 init.sql 等脚本
pip install -r requirements.txt
python start.py
```

方式B：Docker 启动包含 API 在内的全栈后端

```bash
cd udbm-backend
docker-compose up -d                   # 将启动 postgres、redis、api
```

方式C：启动前端

```bash
cd udbm-frontend
npm install
npm start
```

前端默认通过 CRA 代理连接后端，也可设置环境变量：

```bash
export REACT_APP_API_BASE_URL="http://localhost:8000/api/v1"
```

### 3. 访问应用

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health 或 http://localhost:8000/api/v1/health/

## 🎮 使用演示

### 数据库实例管理

1. **添加数据库实例**
   - 点击"添加数据库"按钮
   - 填写数据库连接信息
   - 选择数据库类型和环境

2. **测试连接**
   - 点击数据库列表中的测试按钮
   - 查看连接状态和响应时间

3. **查看详情**
   - 点击数据库名称查看详细信息
   - 查看连接信息和配置详情

## 🔧 核心功能演示

### 数据库连接测试

```python
# 测试PostgreSQL连接
result = await DatabaseConnectionService.test_connection(
    db_type="postgresql",
    host="localhost",
    port=5432,
    database="postgres",
    username="postgres",
    password="password"
)
print(f"连接成功: {result.success}, 响应时间: {result.response_time}s")
```

### API调用示例

```bash
# 获取数据库列表
curl http://localhost:8000/api/v1/databases/

# 创建数据库实例
curl -X POST http://localhost:8000/api/v1/databases/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "演示数据库",
    "type_id": 1,
    "host": "localhost",
    "port": 5432,
    "database_name": "demo",
    "environment": "development"
  }'

# 测试数据库连接（注意为 POST 方法）
curl -X POST http://localhost:8000/api/v1/databases/1/test-connection
```

## 📊 数据库设计

### 核心数据表

- **users**: 用户信息表
- **database_instances**: 数据库实例表
- **database_types**: 数据库类型表
- **metric_definitions**: 监控指标定义表
- **metrics**: 监控指标数据表
- **alert_rules**: 告警规则表
- **alerts**: 告警历史表
- **backup_policies**: 备份策略表
- **backup_tasks**: 备份任务表

### 数据关系

```
users ──┬──► user_roles ◄──┬── roles
        │                  │
        └──────────────────┼──► role_permissions ──► permissions
                           │
database_instances ◄──────┼──► database_groups
        │                 │
        ├─► metrics ──────┼──► metric_definitions
        ├─► alerts ───────┼──► alert_rules
        └─► backup_tasks ─┼──► backup_policies
```

## 🛠️ 开发工具

### 后端开发

```bash
cd udbm-backend

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python start.py
```

### 前端开发

```bash
cd udbm-frontend

# 安装依赖
npm install

# 启动开发服务器
npm start

# 构建生产版本
npm run build
```

## 🔍 监控和调试

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/api/v1/health/

# 数据库健康检查
curl http://localhost:8000/api/v1/health/database

# 详细健康检查
curl http://localhost:8000/api/v1/health/detailed
```

### 日志查看

```bash
# 查看后端日志
docker-compose logs -f api

# 查看数据库日志
docker-compose logs -f postgres
```

## 🎯 MVP里程碑

- [x] **Phase 1**: 项目基础架构搭建
- [x] **Phase 2**: 数据库实例管理功能
- [x] **Phase 3**: 前端界面开发
- [x] **Phase 4**: 连接测试功能
- [ ] **Phase 5**: 用户权限管理系统
- [ ] **Phase 6**: 监控和告警功能
- [ ] **Phase 7**: 备份恢复功能
- [ ] **Phase 8**: 生产环境部署

## 🌟 亮点特性

1. **现代化技术栈**: 使用最新的React 18、FastAPI、SQLAlchemy 2.0
2. **完整的API设计**: RESTful API + 自动生成的OpenAPI文档
3. **响应式前端**: 适配桌面和移动设备的现代化界面
4. **类型安全**: 后端使用Pydantic进行数据验证
5. **异步编程**: 后端采用async/await模式提升性能
6. **容器化支持**: 完整的Docker配置便于部署

## 📈 性能指标

- **API响应时间**: < 100ms (本地环境)
- **数据库连接测试**: < 500ms
- **前端页面加载**: < 2s
- **内存占用**: < 200MB (基础配置)

## 🤝 贡献指南

我们欢迎任何形式的贡献！

1. **报告问题**: 在GitHub Issues中报告bug或建议新功能
2. **代码贡献**: 提交Pull Request改进代码
3. **文档完善**: 帮助完善项目文档
4. **功能测试**: 测试新功能并提供反馈

## 📄 许可证

本项目采用 MIT 许可证 - 详见各子项目的LICENSE文件

## 🎉 致谢

感谢所有为这个疯狂项目贡献力量的人们！我们正在用AI驱动的方式重新定义数据库管理平台的开发方式。

---

**让我们一起干一件疯狂的事情！** 🚀
