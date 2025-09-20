-- UDBM 数据库初始化脚本
-- 统一数据库管理平台

-- 创建数据库（如果不存在）
-- 注意：在Docker中，这个脚本会在数据库创建时自动执行

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_buffercache";
CREATE EXTENSION IF NOT EXISTS "pg_prewarm";

-- 创建udbm模式
CREATE SCHEMA IF NOT EXISTS udbm;
SET search_path TO udbm, public;

-- 用户表
CREATE TABLE IF NOT EXISTS udbm.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    department VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'dba', 'operator', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

-- 角色表
CREATE TABLE IF NOT EXISTS udbm.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '{}',
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS udbm.user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES udbm.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES udbm.roles(id) ON DELETE CASCADE,
    granted_by INTEGER REFERENCES udbm.users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(user_id, role_id)
);

-- 权限表
CREATE TABLE IF NOT EXISTS udbm.permissions (
    id SERIAL PRIMARY KEY,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, action)
);

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS udbm.role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES udbm.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES udbm.permissions(id) ON DELETE CASCADE,
    granted_by INTEGER REFERENCES udbm.users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);

-- 数据库类型表
CREATE TABLE IF NOT EXISTS udbm.database_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    driver_class VARCHAR(200),
    default_port INTEGER,
    supported_features JSONB DEFAULT '{}',
    config_template JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据库实例表
CREATE TABLE IF NOT EXISTS udbm.database_instances (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type_id INTEGER NOT NULL REFERENCES udbm.database_types(id),
    host VARCHAR(100) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(100),
    username VARCHAR(50),
    password_encrypted TEXT,
    ssl_enabled BOOLEAN DEFAULT false,
    ssl_config JSONB DEFAULT '{}',
    connection_params JSONB DEFAULT '{}',
    tags JSONB DEFAULT '{}',
    environment VARCHAR(20) DEFAULT 'production' CHECK (environment IN ('development', 'staging', 'production')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'warning', 'critical', 'unknown')),
    last_health_check TIMESTAMP,
    health_check_config JSONB DEFAULT '{}',
    created_by INTEGER REFERENCES udbm.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据库分组表
CREATE TABLE IF NOT EXISTS udbm.database_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES udbm.database_groups(id),
    level INTEGER DEFAULT 1,
    path VARCHAR(1000),
    created_by INTEGER REFERENCES udbm.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据库分组成员表
CREATE TABLE IF NOT EXISTS udbm.database_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES udbm.database_groups(id) ON DELETE CASCADE,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id) ON DELETE CASCADE,
    added_by INTEGER REFERENCES udbm.users(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, database_id)
);

-- 监控指标定义表
CREATE TABLE IF NOT EXISTS udbm.metric_definitions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    unit VARCHAR(50),
    metric_type VARCHAR(20) DEFAULT 'gauge' CHECK (metric_type IN ('gauge', 'counter', 'histogram', 'summary')),
    data_type VARCHAR(20) DEFAULT 'numeric' CHECK (data_type IN ('numeric', 'text', 'boolean')),
    database_types TEXT[],
    collection_interval INTEGER DEFAULT 60,
    retention_days INTEGER DEFAULT 90,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 监控指标数据表
CREATE TABLE IF NOT EXISTS udbm.metrics (
    time TIMESTAMPTZ NOT NULL,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id),
    metric_id INTEGER NOT NULL REFERENCES udbm.metric_definitions(id),
    value_numeric DOUBLE PRECISION,
    value_text TEXT,
    value_boolean BOOLEAN,
    tags JSONB DEFAULT '{}',
    quality_score INTEGER DEFAULT 100 CHECK (quality_score >= 0 AND quality_score <= 100)
);

-- 设置复合主键
ALTER TABLE udbm.metrics DROP CONSTRAINT IF EXISTS metrics_pkey;
ALTER TABLE udbm.metrics ADD PRIMARY KEY (time, database_id, metric_id);

-- 告警规则表
CREATE TABLE IF NOT EXISTS udbm.alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    metric_id INTEGER REFERENCES udbm.metric_definitions(id),
    database_id INTEGER REFERENCES udbm.database_instances(id),
    condition_operator VARCHAR(10) CHECK (condition_operator IN ('>', '<', '>=', '<=', '==', '!=')),
    condition_value DOUBLE PRECISION,
    severity VARCHAR(20) DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    evaluation_period INTEGER DEFAULT 300,
    notification_channels JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES udbm.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 告警历史表
CREATE TABLE IF NOT EXISTS udbm.alerts (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES udbm.alert_rules(id),
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id),
    metric_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'firing' CHECK (status IN ('firing', 'resolved', 'acknowledged')),
    description TEXT,
    labels JSONB DEFAULT '{}',
    annotations JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    acknowledged_by INTEGER REFERENCES udbm.users(id),
    acknowledged_at TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON udbm.users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON udbm.users (email);
CREATE INDEX IF NOT EXISTS idx_users_department ON udbm.users (department);
CREATE INDEX IF NOT EXISTS idx_users_role_active ON udbm.users (role, is_active);

CREATE INDEX IF NOT EXISTS idx_db_instances_type_status ON udbm.database_instances (type_id, status);
CREATE INDEX IF NOT EXISTS idx_db_instances_host_port ON udbm.database_instances (host, port);
CREATE INDEX IF NOT EXISTS idx_db_instances_environment ON udbm.database_instances (environment);
CREATE INDEX IF NOT EXISTS idx_db_instances_health ON udbm.database_instances (health_status, last_health_check);

CREATE INDEX IF NOT EXISTS idx_metrics_database_time ON udbm.metrics (database_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_metric_time ON udbm.metrics (metric_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_tags ON udbm.metrics USING GIN (tags);

CREATE INDEX IF NOT EXISTS idx_alerts_status_started ON udbm.alerts (status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_database_status ON udbm.alerts (database_id, status, started_at DESC);

-- 插入基础数据
INSERT INTO udbm.database_types (name, display_name, driver_class, default_port, supported_features, config_template) VALUES
('postgresql', 'PostgreSQL', 'postgresql+asyncpg', 5432,
 '{"backup": true, "monitoring": true, "query_analysis": true, "performance_tuning": true}',
 '{"connection_timeout": 30, "command_timeout": 60}'),
('mysql', 'MySQL', 'mysql+pymysql', 3306,
 '{"backup": true, "monitoring": true, "query_analysis": true, "performance_tuning": true}',
 '{"connection_timeout": 30, "command_timeout": 60}'),
('oceanbase', 'OceanBase', 'mysql+pymysql', 2881,
 '{"backup": true, "monitoring": true, "query_analysis": true, "performance_tuning": true}',
 '{"connection_timeout": 30, "command_timeout": 60, "tenant": "sys"}'),
('mongodb', 'MongoDB', 'mongodb', 27017,
 '{"backup": true, "monitoring": true, "query_analysis": false, "performance_tuning": true}',
 '{"connection_timeout": 30, "server_selection_timeout": 30}'),
('redis', 'Redis', 'redis', 6379,
 '{"backup": true, "monitoring": true, "query_analysis": false, "performance_tuning": false}',
 '{"connection_timeout": 30, "socket_timeout": 30}')
ON CONFLICT (name) DO NOTHING;

-- 插入基础权限
INSERT INTO udbm.permissions (resource, action, description) VALUES
('database', 'read', '查看数据库实例'),
('database', 'write', '管理数据库实例'),
('database', 'delete', '删除数据库实例'),
('monitoring', 'read', '查看监控数据'),
('monitoring', 'write', '配置监控规则'),
('backup', 'read', '查看备份任务'),
('backup', 'write', '创建备份任务'),
('user', 'read', '查看用户信息'),
('user', 'write', '管理用户'),
('system', 'admin', '系统管理权限')
ON CONFLICT (resource, action) DO NOTHING;

-- 插入基础角色
INSERT INTO udbm.roles (name, description, permissions, is_system) VALUES
('admin', '系统管理员', '{"database": ["read", "write", "delete"], "monitoring": ["read", "write"], "backup": ["read", "write"], "user": ["read", "write"], "system": ["admin"]}', true),
('dba', '数据库管理员', '{"database": ["read", "write"], "monitoring": ["read", "write"], "backup": ["read", "write"], "user": ["read"]}', true),
('operator', '运维工程师', '{"database": ["read", "write"], "monitoring": ["read"], "backup": ["read", "write"]}', true),
('viewer', '只读用户', '{"database": ["read"], "monitoring": ["read"], "backup": ["read"]}', true)
ON CONFLICT (name) DO NOTHING;

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION udbm.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表创建更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON udbm.users FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
CREATE TRIGGER update_database_instances_updated_at BEFORE UPDATE ON udbm.database_instances FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON udbm.alert_rules FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();

-- 创建默认管理员用户 (密码: admin123)
-- 注意：实际部署时应该使用更安全的方式创建初始用户
-- INSERT INTO udbm.users (username, email, password_hash, full_name, role, is_active)
-- VALUES ('admin', 'admin@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfLkIwWQXjZzQaO', '系统管理员', 'admin', true)
-- ON CONFLICT (username) DO NOTHING;
