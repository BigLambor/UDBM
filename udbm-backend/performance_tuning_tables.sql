-- 性能调优相关表结构
-- 需要添加到数据库中的表

-- 慢查询记录表
CREATE TABLE IF NOT EXISTS udbm.slow_queries (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    execution_time DOUBLE PRECISION NOT NULL,
    lock_time DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    rows_sent BIGINT DEFAULT 0 NOT NULL,
    rows_examined BIGINT DEFAULT 0 NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_host VARCHAR(200),
    sql_command VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' NOT NULL CHECK (status IN ('active', 'resolved', 'ignored')),
    analysis_result TEXT,
    optimization_suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 性能指标表
CREATE TABLE IF NOT EXISTS udbm.performance_metrics (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    tags TEXT DEFAULT '{}' NOT NULL,
    metric_metadata TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引建议表
CREATE TABLE IF NOT EXISTS udbm.index_suggestions (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    column_names TEXT NOT NULL,
    index_type VARCHAR(50) DEFAULT 'btree' NOT NULL,
    suggestion_type VARCHAR(50) NOT NULL CHECK (suggestion_type IN ('missing', 'redundant', 'unused', 'inefficient')),
    reason TEXT NOT NULL,
    impact_score DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    estimated_improvement TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'applied', 'rejected', 'failed')),
    applied_at TIMESTAMP,
    applied_by INTEGER,
    related_query_ids TEXT DEFAULT '[]' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 执行计划分析表
CREATE TABLE IF NOT EXISTS udbm.execution_plans (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    plan_json TEXT NOT NULL,
    plan_text TEXT NOT NULL,
    cost_estimate DOUBLE PRECISION,
    rows_estimate BIGINT,
    actual_rows BIGINT,
    execution_time DOUBLE PRECISION,
    analysis_result TEXT,
    optimization_suggestions TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 调优任务表
CREATE TABLE IF NOT EXISTS udbm.tuning_tasks (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('index_creation', 'query_rewrite', 'config_tuning', 'vacuum', 'analyze', 'reindex')),
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    task_config TEXT NOT NULL,
    execution_sql TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 1 NOT NULL CHECK (priority >= 1 AND priority <= 5),
    execution_result TEXT,
    error_message TEXT,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    related_suggestion_id INTEGER,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统诊断报告表
CREATE TABLE IF NOT EXISTS udbm.system_diagnoses (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL REFERENCES udbm.database_instances(id) ON DELETE CASCADE,
    diagnosis_type VARCHAR(50) NOT NULL CHECK (diagnosis_type IN ('full', 'quick', 'specific')),
    overall_score DOUBLE PRECISION NOT NULL,
    diagnosis_result TEXT NOT NULL,
    recommendations TEXT,
    performance_score DOUBLE PRECISION NOT NULL,
    security_score DOUBLE PRECISION NOT NULL,
    maintenance_score DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_slow_queries_database_id ON udbm.slow_queries (database_id);
CREATE INDEX IF NOT EXISTS idx_slow_queries_query_hash ON udbm.slow_queries (query_hash);
CREATE INDEX IF NOT EXISTS idx_slow_queries_timestamp ON udbm.slow_queries (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_slow_queries_execution_time ON udbm.slow_queries (execution_time DESC);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_database_id ON udbm.performance_metrics (database_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON udbm.performance_metrics (metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON udbm.performance_metrics (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_index_suggestions_database_id ON udbm.index_suggestions (database_id);
CREATE INDEX IF NOT EXISTS idx_index_suggestions_table_name ON udbm.index_suggestions (table_name);
CREATE INDEX IF NOT EXISTS idx_index_suggestions_status ON udbm.index_suggestions (status);
CREATE INDEX IF NOT EXISTS idx_index_suggestions_impact_score ON udbm.index_suggestions (impact_score DESC);

CREATE INDEX IF NOT EXISTS idx_execution_plans_database_id ON udbm.execution_plans (database_id);
CREATE INDEX IF NOT EXISTS idx_execution_plans_query_hash ON udbm.execution_plans (query_hash);
CREATE INDEX IF NOT EXISTS idx_execution_plans_timestamp ON udbm.execution_plans (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_tuning_tasks_database_id ON udbm.tuning_tasks (database_id);
CREATE INDEX IF NOT EXISTS idx_tuning_tasks_status ON udbm.tuning_tasks (status);
CREATE INDEX IF NOT EXISTS idx_tuning_tasks_priority ON udbm.tuning_tasks (priority DESC);
CREATE INDEX IF NOT EXISTS idx_tuning_tasks_created_at ON udbm.tuning_tasks (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_system_diagnoses_database_id ON udbm.system_diagnoses (database_id);
CREATE INDEX IF NOT EXISTS idx_system_diagnoses_timestamp ON udbm.system_diagnoses (timestamp DESC);

-- 为表创建更新时间触发器
CREATE TRIGGER update_slow_queries_updated_at BEFORE UPDATE ON udbm.slow_queries FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
CREATE TRIGGER update_performance_metrics_updated_at BEFORE UPDATE ON udbm.performance_metrics FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
CREATE TRIGGER update_index_suggestions_updated_at BEFORE UPDATE ON udbm.index_suggestions FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
CREATE TRIGGER update_execution_plans_updated_at BEFORE UPDATE ON udbm.execution_plans FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
CREATE TRIGGER update_tuning_tasks_updated_at BEFORE UPDATE ON udbm.tuning_tasks FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
CREATE TRIGGER update_system_diagnoses_updated_at BEFORE UPDATE ON udbm.system_diagnoses FOR EACH ROW EXECUTE FUNCTION udbm.update_updated_at_column();
