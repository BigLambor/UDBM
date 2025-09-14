-- MySQL 性能调优相关表结构
-- 适配MySQL 8.0语法

USE udbm_mysql_demo;

-- 创建udbm schema（如果不存在）
-- MySQL中schema就是database，所以直接使用udbm_mysql_demo数据库

-- 慢查询记录表
CREATE TABLE IF NOT EXISTS slow_queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    database_id INT NOT NULL,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    execution_time DOUBLE NOT NULL,
    lock_time DOUBLE DEFAULT 0.0 NOT NULL,
    rows_sent BIGINT DEFAULT 0 NOT NULL,
    rows_examined BIGINT DEFAULT 0 NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_host VARCHAR(200),
    sql_command VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' NOT NULL CHECK (status IN ('active', 'resolved', 'ignored')),
    analysis_result TEXT,
    optimization_suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_query_hash (query_hash),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_execution_time (execution_time DESC)
);

-- 性能指标表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    database_id INT NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE NOT NULL,
    unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    tags JSON DEFAULT ('{}') NOT NULL,
    metric_metadata JSON DEFAULT ('{}') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_metric_type (metric_type),
    INDEX idx_timestamp (timestamp DESC)
);

-- 索引建议表
CREATE TABLE IF NOT EXISTS index_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    database_id INT NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    column_names JSON NOT NULL,
    index_type VARCHAR(50) DEFAULT 'btree' NOT NULL,
    suggestion_type VARCHAR(50) NOT NULL CHECK (suggestion_type IN ('missing', 'redundant', 'unused', 'inefficient')),
    reason TEXT NOT NULL,
    impact_score DOUBLE DEFAULT 0.0 NOT NULL,
    estimated_improvement TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'applied', 'rejected', 'failed')),
    applied_at TIMESTAMP NULL,
    applied_by INT NULL,
    related_query_ids JSON DEFAULT ('[]') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_table_name (table_name),
    INDEX idx_status (status),
    INDEX idx_impact_score (impact_score DESC)
);

-- 执行计划分析表
CREATE TABLE IF NOT EXISTS execution_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    database_id INT NOT NULL,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    plan_json JSON NOT NULL,
    plan_text TEXT NOT NULL,
    cost_estimate DOUBLE NULL,
    rows_estimate BIGINT NULL,
    actual_rows BIGINT NULL,
    execution_time DOUBLE NULL,
    analysis_result JSON NULL,
    optimization_suggestions TEXT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_query_hash (query_hash),
    INDEX idx_timestamp (timestamp DESC)
);

-- 调优任务表
CREATE TABLE IF NOT EXISTS tuning_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    database_id INT NOT NULL,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('index_creation', 'query_rewrite', 'config_tuning', 'vacuum', 'analyze', 'reindex')),
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    task_config JSON NOT NULL,
    execution_sql TEXT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INT DEFAULT 1 NOT NULL CHECK (priority >= 1 AND priority <= 5),
    execution_result TEXT NULL,
    error_message TEXT NULL,
    scheduled_at TIMESTAMP NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    related_suggestion_id INT NULL,
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority DESC),
    INDEX idx_created_at (created_at DESC)
);

-- 系统诊断报告表
CREATE TABLE IF NOT EXISTS system_diagnoses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    database_id INT NOT NULL,
    diagnosis_type VARCHAR(50) NOT NULL CHECK (diagnosis_type IN ('full', 'quick', 'specific')),
    overall_score DOUBLE NOT NULL,
    diagnosis_result JSON NOT NULL,
    recommendations TEXT NULL,
    performance_score DOUBLE NOT NULL,
    security_score DOUBLE NOT NULL,
    maintenance_score DOUBLE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_database_id (database_id),
    INDEX idx_timestamp (timestamp DESC)
);

-- 创建数据库实例表（如果不存在）
CREATE TABLE IF NOT EXISTS database_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    db_type VARCHAR(20) NOT NULL,
    host VARCHAR(100) NOT NULL,
    port INT NOT NULL,
    database_name VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_db_type (db_type),
    INDEX idx_is_active (is_active)
);

-- 插入默认的MySQL数据库实例记录
INSERT IGNORE INTO database_instances (id, name, db_type, host, port, database_name, username, password, is_active) 
VALUES (1, 'UDBM MySQL Demo Database', 'mysql', 'localhost', 3306, 'udbm_mysql_demo', 'udbm_mysql_user', 'udbm_mysql_password', TRUE);

-- 创建一些有用的视图
CREATE OR REPLACE VIEW slow_query_summary AS
SELECT 
    database_id,
    COUNT(*) as total_queries,
    AVG(execution_time) as avg_execution_time,
    MAX(execution_time) as max_execution_time,
    COUNT(CASE WHEN execution_time > 2.0 THEN 1 END) as slow_queries_count,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_queries,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_queries
FROM slow_queries
GROUP BY database_id;

CREATE OR REPLACE VIEW performance_metrics_summary AS
SELECT 
    database_id,
    metric_type,
    COUNT(*) as metric_count,
    AVG(metric_value) as avg_value,
    MAX(metric_value) as max_value,
    MIN(metric_value) as min_value,
    MAX(timestamp) as latest_timestamp
FROM performance_metrics
GROUP BY database_id, metric_type;

CREATE OR REPLACE VIEW index_suggestions_summary AS
SELECT 
    database_id,
    suggestion_type,
    status,
    COUNT(*) as suggestion_count,
    AVG(impact_score) as avg_impact_score,
    MAX(impact_score) as max_impact_score
FROM index_suggestions
GROUP BY database_id, suggestion_type, status;

-- 创建存储过程用于清理旧数据
DELIMITER //

CREATE PROCEDURE CleanupOldPerformanceData(IN days_to_keep INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 清理旧的性能指标数据
    DELETE FROM performance_metrics 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    -- 清理旧的慢查询数据（保留已解决的）
    DELETE FROM slow_queries 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY)
    AND status = 'active';
    
    -- 清理旧的执行计划数据
    DELETE FROM execution_plans 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    COMMIT;
    
    SELECT CONCAT('清理完成，删除了 ', days_to_keep, ' 天前的数据') as result;
END //

DELIMITER ;

-- 创建触发器用于自动更新updated_at字段
DELIMITER //

CREATE TRIGGER update_slow_queries_updated_at 
    BEFORE UPDATE ON slow_queries 
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER update_performance_metrics_updated_at 
    BEFORE UPDATE ON performance_metrics 
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER update_index_suggestions_updated_at 
    BEFORE UPDATE ON index_suggestions 
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER update_execution_plans_updated_at 
    BEFORE UPDATE ON execution_plans 
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER update_tuning_tasks_updated_at 
    BEFORE UPDATE ON tuning_tasks 
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER update_system_diagnoses_updated_at 
    BEFORE UPDATE ON system_diagnoses 
    FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

DELIMITER ;

-- 输出创建完成信息
SELECT 'MySQL性能调优表结构创建完成！' as message;
SELECT 'UDBM MySQL性能监控环境已准备就绪' as status;
