-- OceanBase 简化示例数据
-- 避免复杂的JSON语法问题

USE udbm_oceanbase_demo;

-- 插入一些基本的慢查询数据
INSERT IGNORE INTO slow_queries (
    database_id, query_text, query_hash, execution_time, lock_time, 
    rows_sent, rows_examined, user_host, sql_command
) VALUES
(1, 'SELECT * FROM products WHERE price > 1000', 'hash001', 2.45, 0.02, 100, 5000, 'app@192.168.1.100', 'SELECT'),
(1, 'UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id = 123', 'hash002', 1.87, 0.15, 0, 1200, 'app@192.168.1.101', 'UPDATE'),
(1, 'SELECT COUNT(*) FROM orders WHERE created_at > NOW() - INTERVAL 1 DAY', 'hash003', 3.21, 0.08, 25, 8000, 'report@192.168.1.102', 'SELECT');

-- 插入基本的性能指标数据
INSERT IGNORE INTO performance_metrics (
    database_id, metric_type, metric_name, metric_value, unit, tags, metric_metadata
) VALUES
(1, 'cpu', 'usage_percent', 65.5, '%', '{}', '{}'),
(1, 'memory', 'used_mb', 24576, 'MB', '{}', '{}'),
(1, 'connections', 'active_connections', 125, 'count', '{}', '{}'),
(1, 'throughput', 'qps', 1250.5, 'queries/sec', '{}', '{}');

-- 插入基本的调优任务数据
INSERT IGNORE INTO tuning_tasks (
    database_id, task_type, title, description, priority, status, 
    estimated_duration, progress, parameters, results, created_by
) VALUES
(1, 'index_optimization', '优化产品查询索引', '为products表创建索引', 'high', 'completed', 30, 100, '{}', '{}', 1),
(1, 'memory_optimization', 'OceanBase内存配置优化', '调整内存配置', 'medium', 'pending', 45, 0, '{}', '{}', 1);

-- 插入基本的调优建议数据
INSERT IGNORE INTO tuning_recommendations (
    database_id, category, subcategory, title, description, priority, 
    impact_score, confidence_score, estimated_improvement, implementation_difficulty,
    sql_script, related_metrics, created_by
) VALUES
(1, 'indexing', 'missing_index', '为products表添加price索引', '检测到price字段查询频繁，建议添加索引', 'high', 85, 90, '查询性能提升40-60%', 'low', 'CREATE INDEX idx_products_price ON products(price);', '{}', 1),
(1, 'memory', 'plan_cache', '增加计划缓存内存', '计划缓存命中率较低，建议增加内存分配', 'medium', 60, 80, '命中率提升到95%+', 'low', 'ALTER SYSTEM SET plan_cache_mem_limit = ''4G'';', '{}', 2);

-- 插入基本的索引分析数据
INSERT IGNORE INTO index_analysis (
    database_id, table_name, index_name, index_type, columns, 
    cardinality, size_mb, usage_count, recommendation, reason
) VALUES
(1, 'products', 'PRIMARY', 'BTREE', 'id', 10000, 15.2, 50000, 'keep', '主键索引，必须保留'),
(1, 'products', 'idx_name', 'BTREE', 'name', 9800, 12.8, 1200, 'keep', '名称查询频繁使用'),
(1, 'products', 'idx_status', 'BTREE', 'status', 3, 5.2, 50, 'drop', '使用频率极低，选择性差');

-- 插入基本的系统监控数据
INSERT IGNORE INTO system_monitoring (
    database_id, monitoring_type, metric_name, metric_value, unit, 
    threshold_warning, threshold_critical, status, additional_info
) VALUES
(1, 'cpu', 'cpu_usage_percent', 65.5, '%', 80.0, 90.0, 'normal', '{}'),
(1, 'memory', 'memory_usage_percent', 75.2, '%', 85.0, 95.0, 'normal', '{}'),
(1, 'io', 'disk_usage_percent', 68.8, '%', 80.0, 90.0, 'normal', '{}');

-- 插入OceanBase特定监控数据
INSERT IGNORE INTO oceanbase_monitoring (
    database_id, tenant_name, plan_cache_hit_ratio, plan_cache_mem_used_mb, 
    rpc_queue_len, major_compaction_progress, tenant_mem_used_mb, 
    memstore_used_mb, tablet_count, log_disk_usage_percent
) VALUES
(1, 'udbm_ob_tenant', 92.5, 1800, 8, 85.6, 18432, 3072, 2500, 45.2),
(1, 'udbm_ob_tenant', 91.8, 1850, 12, 86.1, 18650, 3150, 2505, 46.1);

-- 插入告警规则数据
INSERT IGNORE INTO alert_rules (
    database_id, rule_name, metric_type, metric_name, condition_operator,
    threshold_warning, threshold_critical, notification_channels, created_by
) VALUES
(1, 'CPU使用率告警', 'cpu', 'usage_percent', '>', 80.0, 90.0, '[]', 1),
(1, '内存使用率告警', 'memory', 'usage_percent', '>', 85.0, 95.0, '[]', 1);

COMMIT;
