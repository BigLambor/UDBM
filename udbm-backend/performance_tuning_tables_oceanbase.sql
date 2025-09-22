-- OceanBase 性能调优相关表结构
-- 适配OceanBase语法

USE udbm_oceanbase_demo;

-- 慢查询记录表
CREATE TABLE IF NOT EXISTS slow_queries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    query_text LONGTEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    execution_time DOUBLE NOT NULL,
    lock_time DOUBLE DEFAULT 0.0 NOT NULL,
    rows_sent BIGINT DEFAULT 0 NOT NULL,
    rows_examined BIGINT DEFAULT 0 NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_host VARCHAR(200),
    sql_command VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    analysis_result LONGTEXT,
    optimization_suggestions LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_query_hash (query_hash),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_execution_time (execution_time DESC)
);

-- 性能指标表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE NOT NULL,
    unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    tags JSON NOT NULL,
    metric_metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_metric_type (metric_type),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_metric_name (metric_name)
);

-- 性能调优任务表
CREATE TABLE IF NOT EXISTS tuning_tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description LONGTEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to BIGINT,
    estimated_duration INT, -- 预计耗时（分钟）
    actual_duration INT,    -- 实际耗时（分钟）
    progress INT DEFAULT 0, -- 进度百分比
    parameters JSON NOT NULL,
    results JSON NOT NULL,
    error_message LONGTEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT,
    INDEX idx_database_id (database_id),
    INDEX idx_task_type (task_type),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at DESC)
);

-- 性能调优建议表
CREATE TABLE IF NOT EXISTS tuning_recommendations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    description LONGTEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    impact_score INT DEFAULT 50, -- 影响评分 0-100
    confidence_score INT DEFAULT 50, -- 置信度评分 0-100
    estimated_improvement VARCHAR(100), -- 预期改善效果
    implementation_difficulty VARCHAR(20) DEFAULT 'medium',
    sql_script LONGTEXT, -- 执行脚本
    rollback_script LONGTEXT, -- 回滚脚本
    related_metrics JSON NOT NULL,
    prerequisites LONGTEXT, -- 前置条件
    risks LONGTEXT, -- 风险说明
    status VARCHAR(20) DEFAULT 'active',
    applied_at TIMESTAMP NULL,
    applied_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT,
    INDEX idx_database_id (database_id),
    INDEX idx_category (category),
    INDEX idx_priority (priority),
    INDEX idx_impact_score (impact_score DESC),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);

-- 索引分析表
CREATE TABLE IF NOT EXISTS index_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    index_name VARCHAR(100),
    index_type VARCHAR(50),
    columns LONGTEXT NOT NULL,
    cardinality BIGINT,
    size_mb DOUBLE,
    usage_count BIGINT DEFAULT 0,
    last_used TIMESTAMP NULL,
    redundant_with VARCHAR(100), -- 冗余索引
    recommendation VARCHAR(50), -- 'keep', 'drop', 'modify', 'create'
    reason LONGTEXT,
    impact_analysis LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_table_name (table_name),
    INDEX idx_recommendation (recommendation),
    INDEX idx_usage_count (usage_count DESC)
);

-- 执行计划分析表
CREATE TABLE IF NOT EXISTS execution_plan_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    query_text LONGTEXT NOT NULL,
    plan_hash VARCHAR(64),
    execution_plan LONGTEXT NOT NULL,
    cost_estimate DOUBLE,
    execution_time DOUBLE,
    rows_processed BIGINT,
    buffer_reads BIGINT,
    disk_reads BIGINT,
    cpu_time DOUBLE,
    wait_time DOUBLE,
    plan_stability VARCHAR(20), -- 'stable', 'unstable', 'new'
    optimization_opportunities LONGTEXT,
    recommended_hints LONGTEXT,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_query_hash (query_hash),
    INDEX idx_plan_hash (plan_hash),
    INDEX idx_cost_estimate (cost_estimate DESC),
    INDEX idx_execution_time (execution_time DESC)
);

-- 系统监控数据表
CREATE TABLE IF NOT EXISTS system_monitoring (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    monitoring_type VARCHAR(50) NOT NULL, -- 'cpu', 'memory', 'io', 'network', 'oceanbase'
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE NOT NULL,
    unit VARCHAR(20),
    threshold_warning DOUBLE,
    threshold_critical DOUBLE,
    status VARCHAR(20) DEFAULT 'normal', -- 'normal', 'warning', 'critical'
    alert_sent TINYINT(1) DEFAULT 0,
    additional_info JSON NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_monitoring_type (monitoring_type),
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_status (status)
);

-- OceanBase特定监控表
CREATE TABLE IF NOT EXISTS oceanbase_monitoring (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    tenant_name VARCHAR(100),
    unit_name VARCHAR(100),
    -- 计划缓存相关
    plan_cache_hit_ratio DOUBLE,
    plan_cache_mem_used_mb DOUBLE,
    plan_cache_mem_limit_mb DOUBLE,
    -- RPC相关
    rpc_queue_len BIGINT,
    rpc_timeout_count BIGINT,
    -- 合并相关
    major_compaction_progress DOUBLE,
    minor_compaction_pending BIGINT,
    -- 内存相关
    tenant_mem_used_mb DOUBLE,
    memstore_used_mb DOUBLE,
    tablet_count BIGINT,
    ls_count BIGINT,
    -- 日志相关
    log_disk_usage_percent DOUBLE,
    log_sync_delay_ms DOUBLE,
    -- 事务相关
    active_trans_count BIGINT,
    pending_trans_count BIGINT,
    -- 时间戳
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_tenant_name (tenant_name),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_plan_cache_hit_ratio (plan_cache_hit_ratio),
    INDEX idx_rpc_queue_len (rpc_queue_len)
);

-- 性能基线表
CREATE TABLE IF NOT EXISTS performance_baselines (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    baseline_name VARCHAR(100) NOT NULL,
    baseline_type VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'monthly', 'custom'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    metrics JSON NOT NULL, -- 基线指标数据
    workload_characteristics JSON NOT NULL,
    environment_info JSON NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    notes LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    INDEX idx_database_id (database_id),
    INDEX idx_baseline_type (baseline_type),
    INDEX idx_period (period_start, period_end),
    INDEX idx_is_active (is_active)
);

-- 性能告警规则表
CREATE TABLE IF NOT EXISTS alert_rules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    database_id BIGINT NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    condition_operator VARCHAR(10) NOT NULL, -- '>', '<', '>=', '<=', '=', '!='
    threshold_warning DOUBLE,
    threshold_critical DOUBLE,
    evaluation_window INT DEFAULT 300, -- 评估窗口（秒）
    evaluation_frequency INT DEFAULT 60, -- 评估频率（秒）
    consecutive_breaches INT DEFAULT 1, -- 连续违规次数
    is_enabled TINYINT(1) DEFAULT 1,
    notification_channels JSON NOT NULL, -- 通知渠道
    suppression_duration INT DEFAULT 3600, -- 抑制时长（秒）
    recovery_notification TINYINT(1) DEFAULT 1,
    tags JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT,
    INDEX idx_database_id (database_id),
    INDEX idx_metric_type (metric_type),
    INDEX idx_is_enabled (is_enabled)
);

-- 性能告警历史表
CREATE TABLE IF NOT EXISTS alert_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rule_id BIGINT NOT NULL,
    database_id BIGINT NOT NULL,
    alert_level VARCHAR(20) NOT NULL, -- 'warning', 'critical'
    metric_value DOUBLE NOT NULL,
    threshold_value DOUBLE NOT NULL,
    message LONGTEXT NOT NULL,
    alert_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alert_end TIMESTAMP NULL,
    duration_seconds INT,
    is_resolved TINYINT(1) DEFAULT 0,
    resolution_note LONGTEXT,
    notification_sent TINYINT(1) DEFAULT 0,
    additional_context JSON NOT NULL,
    INDEX idx_rule_id (rule_id),
    INDEX idx_database_id (database_id),
    INDEX idx_alert_level (alert_level),
    INDEX idx_alert_start (alert_start DESC),
    INDEX idx_is_resolved (is_resolved)
);

-- 创建一些性能相关的视图

-- 慢查询统计视图
CREATE OR REPLACE VIEW slow_query_stats AS
SELECT 
    database_id,
    DATE(timestamp) as query_date,
    COUNT(*) as slow_query_count,
    AVG(execution_time) as avg_execution_time,
    MAX(execution_time) as max_execution_time,
    AVG(rows_examined) as avg_rows_examined,
    MAX(rows_examined) as max_rows_examined
FROM slow_queries
WHERE status = 'active'
GROUP BY database_id, DATE(timestamp);

-- 性能指标趋势视图
CREATE OR REPLACE VIEW performance_trends AS
SELECT 
    database_id,
    metric_type,
    metric_name,
    DATE(timestamp) as metric_date,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    COUNT(*) as sample_count
FROM performance_metrics
GROUP BY database_id, metric_type, metric_name, DATE(timestamp);

-- OceanBase监控概览视图
CREATE OR REPLACE VIEW oceanbase_overview AS
SELECT 
    database_id,
    tenant_name,
    AVG(plan_cache_hit_ratio) as avg_plan_cache_hit_ratio,
    AVG(rpc_queue_len) as avg_rpc_queue_len,
    AVG(major_compaction_progress) as avg_major_compaction_progress,
    AVG(tenant_mem_used_mb) as avg_tenant_mem_used_mb,
    AVG(log_disk_usage_percent) as avg_log_disk_usage_percent,
    COUNT(*) as sample_count,
    MAX(timestamp) as last_updated
FROM oceanbase_monitoring
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY database_id, tenant_name;

-- 活跃告警视图
CREATE OR REPLACE VIEW active_alerts AS
SELECT 
    ah.id,
    ar.rule_name,
    ah.database_id,
    ah.alert_level,
    ah.metric_value,
    ah.threshold_value,
    ah.message,
    ah.alert_start,
    TIMESTAMPDIFF(SECOND, ah.alert_start, NOW()) as duration_seconds
FROM alert_history ah
JOIN alert_rules ar ON ah.rule_id = ar.id
WHERE ah.is_resolved = 0
ORDER BY ah.alert_start DESC;

-- 提交事务
COMMIT;
