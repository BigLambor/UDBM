-- 创建锁分析相关表的SQL脚本
-- 适用于PostgreSQL数据库

-- 创建锁事件记录表
CREATE TABLE IF NOT EXISTS udbm.lock_events (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL,
    lock_type VARCHAR(50) NOT NULL,
    lock_mode VARCHAR(20) NOT NULL,
    lock_status VARCHAR(20) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    object_name VARCHAR(200) NOT NULL,
    schema_name VARCHAR(100),
    session_id VARCHAR(100) NOT NULL,
    process_id INTEGER,
    user_name VARCHAR(100),
    host_name VARCHAR(200),
    lock_request_time TIMESTAMP NOT NULL,
    lock_grant_time TIMESTAMP,
    lock_release_time TIMESTAMP,
    wait_duration FLOAT,
    hold_duration FLOAT,
    query_text TEXT,
    query_hash VARCHAR(64),
    blocking_session_id VARCHAR(100),
    blocking_query_text TEXT,
    analysis_result TEXT,
    optimization_suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    FOREIGN KEY (database_id) REFERENCES udbm.database_instances(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lock_events_database_id ON udbm.lock_events(database_id);
CREATE INDEX IF NOT EXISTS idx_lock_events_timestamp ON udbm.lock_events(lock_request_time);
CREATE INDEX IF NOT EXISTS idx_lock_events_session_id ON udbm.lock_events(session_id);
CREATE INDEX IF NOT EXISTS idx_lock_events_object_name ON udbm.lock_events(object_name);

-- 创建锁等待链表
CREATE TABLE IF NOT EXISTS udbm.lock_wait_chains (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL,
    chain_id VARCHAR(100) NOT NULL,
    chain_length INTEGER NOT NULL,
    total_wait_time FLOAT NOT NULL,
    head_session_id VARCHAR(100) NOT NULL,
    head_query_text TEXT,
    head_lock_type VARCHAR(50) NOT NULL,
    head_object_name VARCHAR(200) NOT NULL,
    tail_session_id VARCHAR(100) NOT NULL,
    tail_query_text TEXT,
    tail_lock_type VARCHAR(50) NOT NULL,
    tail_object_name VARCHAR(200) NOT NULL,
    chain_details TEXT NOT NULL,
    severity_level VARCHAR(20) NOT NULL,
    analysis_result TEXT,
    resolution_suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    FOREIGN KEY (database_id) REFERENCES udbm.database_instances(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lock_wait_chains_database_id ON udbm.lock_wait_chains(database_id);
CREATE INDEX IF NOT EXISTS idx_lock_wait_chains_chain_id ON udbm.lock_wait_chains(chain_id);
CREATE INDEX IF NOT EXISTS idx_lock_wait_chains_severity ON udbm.lock_wait_chains(severity_level);

-- 创建锁竞争分析表
CREATE TABLE IF NOT EXISTS udbm.lock_contentions (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    object_name VARCHAR(200) NOT NULL,
    schema_name VARCHAR(100),
    contention_count INTEGER NOT NULL,
    total_wait_time FLOAT NOT NULL,
    avg_wait_time FLOAT NOT NULL,
    max_wait_time FLOAT NOT NULL,
    contention_pattern VARCHAR(50) NOT NULL,
    lock_types TEXT NOT NULL,
    affected_sessions INTEGER NOT NULL,
    affected_queries INTEGER NOT NULL,
    performance_impact FLOAT NOT NULL,
    root_cause TEXT,
    optimization_suggestions TEXT,
    priority_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    FOREIGN KEY (database_id) REFERENCES udbm.database_instances(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lock_contentions_database_id ON udbm.lock_contentions(database_id);
CREATE INDEX IF NOT EXISTS idx_lock_contentions_object_name ON udbm.lock_contentions(object_name);
CREATE INDEX IF NOT EXISTS idx_lock_contentions_priority ON udbm.lock_contentions(priority_level);

-- 创建锁优化任务表
CREATE TABLE IF NOT EXISTS udbm.lock_optimization_tasks (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    task_config TEXT NOT NULL,
    target_objects TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    priority INTEGER DEFAULT 1 NOT NULL,
    execution_sql TEXT,
    execution_result TEXT,
    error_message TEXT,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    related_contention_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    FOREIGN KEY (database_id) REFERENCES udbm.database_instances(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lock_optimization_tasks_database_id ON udbm.lock_optimization_tasks(database_id);
CREATE INDEX IF NOT EXISTS idx_lock_optimization_tasks_status ON udbm.lock_optimization_tasks(status);
CREATE INDEX IF NOT EXISTS idx_lock_optimization_tasks_priority ON udbm.lock_optimization_tasks(priority);

-- 创建锁分析报告表
CREATE TABLE IF NOT EXISTS udbm.lock_analysis_reports (
    id SERIAL PRIMARY KEY,
    database_id INTEGER NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    analysis_period_start TIMESTAMP NOT NULL,
    analysis_period_end TIMESTAMP NOT NULL,
    overall_health_score FLOAT NOT NULL,
    lock_efficiency_score FLOAT NOT NULL,
    contention_severity VARCHAR(20) NOT NULL,
    total_lock_events INTEGER NOT NULL,
    total_wait_time FLOAT NOT NULL,
    deadlock_count INTEGER DEFAULT 0 NOT NULL,
    timeout_count INTEGER DEFAULT 0 NOT NULL,
    hot_objects TEXT,
    report_content TEXT NOT NULL,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    FOREIGN KEY (database_id) REFERENCES udbm.database_instances(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lock_analysis_reports_database_id ON udbm.lock_analysis_reports(database_id);
CREATE INDEX IF NOT EXISTS idx_lock_analysis_reports_type ON udbm.lock_analysis_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_lock_analysis_reports_period ON udbm.lock_analysis_reports(analysis_period_start);

-- 添加注释
COMMENT ON TABLE udbm.lock_events IS '锁事件记录表';
COMMENT ON TABLE udbm.lock_wait_chains IS '锁等待链表';
COMMENT ON TABLE udbm.lock_contentions IS '锁竞争分析表';
COMMENT ON TABLE udbm.lock_optimization_tasks IS '锁优化任务表';
COMMENT ON TABLE udbm.lock_analysis_reports IS '锁分析报告表';

-- 插入示例数据（可选）
INSERT INTO udbm.lock_events (
    database_id, lock_type, lock_mode, lock_status, object_type, object_name,
    session_id, lock_request_time, wait_duration, query_text
) VALUES (
    1, 'table_lock', 'exclusive', 'granted', 'table', 'users',
    'session_001', CURRENT_TIMESTAMP, 0.0, 'UPDATE users SET status = ''active'''
) ON CONFLICT DO NOTHING;

INSERT INTO udbm.lock_events (
    database_id, lock_type, lock_mode, lock_status, object_type, object_name,
    session_id, lock_request_time, wait_duration, query_text
) VALUES (
    1, 'row_lock', 'shared', 'waiting', 'table', 'orders',
    'session_002', CURRENT_TIMESTAMP, 2.5, 'SELECT * FROM orders WHERE user_id = 100'
) ON CONFLICT DO NOTHING;

-- 创建触发器来自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表添加触发器
CREATE TRIGGER update_lock_events_updated_at BEFORE UPDATE ON udbm.lock_events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lock_wait_chains_updated_at BEFORE UPDATE ON udbm.lock_wait_chains FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lock_contentions_updated_at BEFORE UPDATE ON udbm.lock_contentions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lock_optimization_tasks_updated_at BEFORE UPDATE ON udbm.lock_optimization_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lock_analysis_reports_updated_at BEFORE UPDATE ON udbm.lock_analysis_reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 完成提示
SELECT '锁分析相关表创建完成!' as message;
