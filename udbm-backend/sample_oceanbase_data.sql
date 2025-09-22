-- OceanBase 示例性能数据
-- 为性能调优模块提供测试数据

USE udbm_oceanbase_demo;

-- 插入慢查询示例数据
INSERT IGNORE INTO slow_queries (
    database_id, query_text, query_hash, execution_time, lock_time, 
    rows_sent, rows_examined, user_host, sql_command, analysis_result, 
    optimization_suggestions
) VALUES
(1, 'SELECT * FROM products p JOIN categories c ON p.category_id = c.id WHERE p.price > 1000 ORDER BY p.created_at DESC LIMIT 100', 
 'hash001', 2.45, 0.02, 100, 5000, 'app@192.168.1.100', 'SELECT',
 '{"complexity_score": 65, "efficiency_score": 45, "table_scan_detected": true}',
 '["为price字段添加索引", "优化JOIN条件", "考虑分页查询"]'),

(1, 'UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id IN (SELECT product_id FROM order_items WHERE order_id = 12345)', 
 'hash002', 1.87, 0.15, 0, 1200, 'app@192.168.1.101', 'UPDATE',
 '{"complexity_score": 70, "efficiency_score": 40, "subquery_detected": true}',
 '["使用JOIN替代子查询", "为order_items.order_id添加索引"]'),

(1, 'SELECT u.username, COUNT(o.id) as order_count, SUM(o.total_amount) as total_spent FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id HAVING total_spent > 10000', 
 'hash003', 3.21, 0.08, 25, 8000, 'report@192.168.1.102', 'SELECT',
 '{"complexity_score": 80, "efficiency_score": 35, "group_by_detected": true, "having_clause": true}',
 '["考虑创建汇总表", "为orders.user_id添加索引", "使用物化视图"]'),

(2, 'DELETE FROM audit_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)', 
 'hash004', 5.67, 0.25, 0, 50000, 'cleanup@192.168.1.103', 'DELETE',
 '{"complexity_score": 45, "efficiency_score": 30, "large_dataset": true}',
 '["分批删除数据", "为created_at字段添加索引", "考虑分区表"]);

-- 插入性能指标示例数据
INSERT IGNORE INTO performance_metrics (
    database_id, metric_type, metric_name, metric_value, unit, tags, metric_metadata
) VALUES
-- CPU相关指标
(1, 'cpu', 'usage_percent', 65.5, '%', '{"server": "ob-node-1"}', '{"collection_method": "system"}'),
(1, 'cpu', 'load_average_1m', 2.8, '', '{"server": "ob-node-1"}', '{"collection_method": "system"}'),
(1, 'cpu', 'load_average_5m', 2.1, '', '{"server": "ob-node-1"}', '{"collection_method": "system"}'),

-- 内存相关指标
(1, 'memory', 'total_mb', 32768, 'MB', '{"server": "ob-node-1"}', '{"collection_method": "system"}'),
(1, 'memory', 'used_mb', 24576, 'MB', '{"server": "ob-node-1"}', '{"collection_method": "system"}'),
(1, 'memory', 'usage_percent', 75.0, '%', '{"server": "ob-node-1"}', '{"collection_method": "system"}'),

-- 连接相关指标
(1, 'connections', 'active_connections', 125, 'count', '{"tenant": "udbm_ob_tenant"}', '{"collection_method": "oceanbase"}'),
(1, 'connections', 'idle_connections', 75, 'count', '{"tenant": "udbm_ob_tenant"}', '{"collection_method": "oceanbase"}'),
(1, 'connections', 'max_connections', 512, 'count', '{"tenant": "udbm_ob_tenant"}', '{"collection_method": "oceanbase"}'),

-- 吞吐量相关指标
(1, 'throughput', 'qps', 1250.5, 'queries/sec', '{"tenant": "udbm_ob_tenant"}', '{"collection_method": "oceanbase"}'),
(1, 'throughput', 'tps', 450.2, 'transactions/sec', '{"tenant": "udbm_ob_tenant"}', '{"collection_method": "oceanbase"}'),
(1, 'throughput', 'slow_queries_per_minute', 2.3, 'count/min', '{"tenant": "udbm_ob_tenant"}', '{"collection_method": "oceanbase"}');

-- 插入性能调优任务示例数据
INSERT IGNORE INTO tuning_tasks (
    database_id, task_type, title, description, priority, status, 
    estimated_duration, progress, parameters, results, created_by
) VALUES
(1, 'index_optimization', '优化产品查询索引', '为products表的price和created_at字段创建复合索引', 'high', 'completed',
 30, 100, JSON_OBJECT('table', 'products', 'columns', JSON_ARRAY('price', 'created_at')), 
 JSON_OBJECT('index_created', 'idx_price_created_at', 'performance_improvement', '40%'), 1),

(1, 'slow_query_optimization', '优化用户订单统计查询', '重写用户订单统计查询，使用更高效的JOIN方式', 'medium', 'in_progress',
 60, 75, JSON_OBJECT('query_hash', 'hash003', 'optimization_type', 'rewrite'), 
 JSON_OBJECT('estimated_improvement', '60%', 'current_progress', 'query rewritten, testing in progress'), 1),

(1, 'memory_optimization', 'OceanBase内存配置优化', '调整租户内存限制和计划缓存大小', 'high', 'pending',
 45, 0, JSON_OBJECT('tenant_memory_limit', '32G', 'plan_cache_limit', '4G'), JSON_OBJECT(), 2),

(2, 'compaction_optimization', '合并任务优化', '调整Major Compaction策略，减少对业务的影响', 'medium', 'pending',
 90, 0, JSON_OBJECT('compaction_schedule', '02:00-06:00', 'concurrency', 4), JSON_OBJECT(), 2);

-- 插入性能调优建议示例数据
INSERT IGNORE INTO tuning_recommendations (
    database_id, category, subcategory, title, description, priority, 
    impact_score, confidence_score, estimated_improvement, implementation_difficulty,
    sql_script, related_metrics, prerequisites, risks, created_by
) VALUES
(1, 'indexing', 'missing_index', '为products表添加price索引', 
 '检测到products表的price字段经常用于WHERE条件，但缺少相应索引，建议添加索引以提升查询性能。',
 'high', 85, 90, '查询性能提升40-60%', 'low',
 'CREATE INDEX idx_products_price ON products(price);',
 '{"affected_queries": 15, "avg_execution_time_before": 2.3, "estimated_time_after": 0.9}',
 '确保有足够的磁盘空间用于索引创建', '索引创建期间可能会影响写入性能', 1),

(1, 'query_optimization', 'join_optimization', '优化用户订单关联查询', 
 '用户订单统计查询使用了低效的JOIN方式，建议重写查询逻辑。',
 'high', 75, 85, '查询性能提升50-70%', 'medium',
 'SELECT u.username, COALESCE(stats.order_count, 0) as order_count, COALESCE(stats.total_spent, 0) as total_spent FROM users u LEFT JOIN (SELECT user_id, COUNT(*) as order_count, SUM(total_amount) as total_spent FROM orders GROUP BY user_id) stats ON u.id = stats.user_id WHERE stats.total_spent > 10000;',
 '{"query_hash": "hash003", "current_avg_time": 3.21, "estimated_time": 1.2}',
 '需要测试新查询的正确性', '查询逻辑变更需要充分测试', 1),

(1, 'memory', 'plan_cache', '增加计划缓存内存', 
 '计划缓存命中率较低(88.5%)，建议增加计划缓存内存分配。',
 'medium', 60, 80, '计划缓存命中率提升到95%+', 'low',
 'ALTER SYSTEM SET plan_cache_mem_limit = ''4G'';',
 '{"current_hit_ratio": 88.5, "target_hit_ratio": 95, "current_memory": "2G"}',
 '确保租户有足够的内存资源', '内存增加可能影响其他组件的内存使用', 2),

(1, 'compaction', 'major_compaction', '优化合并策略', 
 'Major Compaction进度较慢，建议调整合并策略和时间窗口。',
 'medium', 55, 75, '合并效率提升30%', 'medium',
 'ALTER SYSTEM SET major_compaction_schedule = ''02:00-06:00''; ALTER SYSTEM SET compaction_concurrency = 4;',
 '{"current_progress": 78.5, "avg_completion_time": "8 hours", "target_time": "6 hours"}',
 '需要在业务低峰期执行', '合并期间可能影响查询性能', 2);

-- 插入索引分析示例数据
INSERT IGNORE INTO index_analysis (
    database_id, table_name, index_name, index_type, columns, 
    cardinality, size_mb, usage_count, last_used, recommendation, reason, impact_analysis
) VALUES
(1, 'products', 'PRIMARY', 'BTREE', 'id', 10000, 15.2, 50000, NOW() - INTERVAL 1 HOUR, 'keep', '主键索引，必须保留', '核心索引，删除会严重影响性能'),
(1, 'products', 'idx_name', 'BTREE', 'name', 9800, 12.8, 1200, NOW() - INTERVAL 2 HOUR, 'keep', '名称查询频繁使用', '中等重要性，建议保留'),
(1, 'products', 'idx_category', 'BTREE', 'category_id', 15, 8.5, 800, NOW() - INTERVAL 5 HOUR, 'keep', '分类查询需要', '用于JOIN查询优化'),
(1, 'products', 'idx_status', 'BTREE', 'status', 3, 5.2, 50, NOW() - INTERVAL 1 DAY, 'drop', '使用频率极低，选择性差', '删除可节省存储空间'),
(1, 'orders', 'idx_user_id', 'BTREE', 'user_id', 1000, 8.9, 2500, NOW() - INTERVAL 30 MINUTE, 'keep', '用户订单查询必需', '高频使用索引'),
(1, 'orders', 'idx_created_at', 'BTREE', 'created_at', 8000, 11.3, 300, NOW() - INTERVAL 3 DAY, 'modify', '可与其他字段组成复合索引', '建议创建复合索引(user_id, created_at)');

-- 插入执行计划分析示例数据
INSERT IGNORE INTO execution_plan_analysis (
    database_id, query_hash, query_text, plan_hash, execution_plan, 
    cost_estimate, execution_time, rows_processed, buffer_reads, disk_reads,
    cpu_time, wait_time, plan_stability, optimization_opportunities, recommended_hints
) VALUES
(1, 'hash001', 'SELECT * FROM products p JOIN categories c ON p.category_id = c.id WHERE p.price > 1000 ORDER BY p.created_at DESC LIMIT 100',
 'plan001', 'NESTED LOOP -> TABLE SCAN products -> INDEX SCAN categories',
 1250.5, 2.45, 100, 5000, 1200, 1.8, 0.65, 'stable',
 '可以为price字段添加索引，使用INDEX SCAN替代TABLE SCAN',
 '/*+ USE_INDEX(p, idx_price_created_at) */'),

(1, 'hash002', 'UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id IN (SELECT product_id FROM order_items WHERE order_id = 12345)',
 'plan002', 'SUBQUERY -> TABLE SCAN order_items -> INDEX LOOKUP products',
 890.2, 1.87, 15, 1200, 800, 1.2, 0.67, 'unstable',
 '将子查询重写为JOIN，可以提升性能',
 '/*+ USE_NL(p, oi) */'),

(1, 'hash003', 'SELECT u.username, COUNT(o.id) as order_count, SUM(o.total_amount) as total_spent FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id HAVING total_spent > 10000',
 'plan003', 'HASH GROUP BY -> HASH LEFT JOIN -> TABLE SCAN users -> INDEX SCAN orders',
 2100.8, 3.21, 25, 8000, 2500, 2.1, 1.11, 'stable',
 '考虑创建汇总表或物化视图，避免实时计算',
 '/*+ USE_HASH(u, o) PARALLEL(4) */');

-- 插入系统监控数据示例
INSERT IGNORE INTO system_monitoring (
    database_id, monitoring_type, metric_name, metric_value, unit, 
    threshold_warning, threshold_critical, status, additional_info
) VALUES
(1, 'cpu', 'cpu_usage_percent', 65.5, '%', 80.0, 90.0, 'normal', '{"cores": 16, "model": "Intel Xeon"}'),
(1, 'memory', 'memory_usage_percent', 75.2, '%', 85.0, 95.0, 'normal', '{"total_gb": 32, "available_gb": 8}'),
(1, 'io', 'disk_usage_percent', 68.8, '%', 80.0, 90.0, 'normal', '{"total_gb": 500, "available_gb": 156}'),
(1, 'io', 'iops', 1250, 'ops/sec', 2000, 3000, 'normal', '{"read_iops": 800, "write_iops": 450}'),
(1, 'network', 'bandwidth_usage_mbps', 45.2, 'Mbps', 80.0, 100.0, 'normal', '{"interface": "eth0", "max_bandwidth": 1000}');

-- 插入OceanBase特定监控数据
INSERT IGNORE INTO oceanbase_monitoring (
    database_id, tenant_name, unit_name, plan_cache_hit_ratio, plan_cache_mem_used_mb, plan_cache_mem_limit_mb,
    rpc_queue_len, rpc_timeout_count, major_compaction_progress, minor_compaction_pending,
    tenant_mem_used_mb, memstore_used_mb, tablet_count, ls_count,
    log_disk_usage_percent, log_sync_delay_ms, active_trans_count, pending_trans_count
) VALUES
(1, 'udbm_ob_tenant', 'unit_001', 92.5, 1800, 2048, 8, 2, 85.6, 12, 
 18432, 3072, 2500, 16, 45.2, 1.2, 125, 5),
(1, 'udbm_ob_tenant', 'unit_001', 91.8, 1850, 2048, 12, 3, 86.1, 15,
 18650, 3150, 2505, 16, 46.1, 1.5, 132, 8),
(1, 'udbm_ob_tenant', 'unit_001', 93.2, 1780, 2048, 6, 1, 86.8, 10,
 18200, 2980, 2498, 16, 44.8, 0.9, 118, 3);

-- 插入性能基线数据
INSERT IGNORE INTO performance_baselines (
    database_id, baseline_name, baseline_type, period_start, period_end,
    metrics, workload_characteristics, environment_info, created_by
) VALUES
(1, '工作日基线', 'daily', '2024-01-15 09:00:00', '2024-01-15 18:00:00',
 '{"avg_qps": 1200, "avg_tps": 450, "avg_cpu": 65, "avg_memory": 75, "plan_cache_hit_ratio": 92.5}',
 '{"peak_hour": "14:00-15:00", "query_types": ["SELECT", "INSERT", "UPDATE"], "concurrent_users": 200}',
 '{"server_specs": "16C/32G", "oceanbase_version": "4.2.1", "tenant_memory": "24G"}', 1),

(1, '周末基线', 'daily', '2024-01-13 10:00:00', '2024-01-13 16:00:00',
 '{"avg_qps": 800, "avg_tps": 300, "avg_cpu": 45, "avg_memory": 60, "plan_cache_hit_ratio": 94.2}',
 '{"peak_hour": "11:00-12:00", "query_types": ["SELECT"], "concurrent_users": 80}',
 '{"server_specs": "16C/32G", "oceanbase_version": "4.2.1", "tenant_memory": "24G"}', 1);

-- 插入告警规则示例数据
INSERT IGNORE INTO alert_rules (
    database_id, rule_name, metric_type, metric_name, condition_operator,
    threshold_warning, threshold_critical, evaluation_window, evaluation_frequency,
    notification_channels, created_by
) VALUES
(1, 'CPU使用率告警', 'cpu', 'usage_percent', '>', 80.0, 90.0, 300, 60,
 '["email:admin@udbm.com", "sms:13800138000"]', 1),
(1, '内存使用率告警', 'memory', 'usage_percent', '>', 85.0, 95.0, 300, 60,
 '["email:admin@udbm.com"]', 1),
(1, '计划缓存命中率告警', 'oceanbase', 'plan_cache_hit_ratio', '<', 90.0, 85.0, 600, 120,
 '["email:dba@udbm.com"]', 2),
(1, 'RPC队列长度告警', 'oceanbase', 'rpc_queue_len', '>', 20, 50, 180, 60,
 '["email:dba@udbm.com", "webhook:http://monitor.udbm.com/alert"]', 2);

-- 插入告警历史示例数据
INSERT IGNORE INTO alert_history (
    rule_id, database_id, alert_level, metric_value, threshold_value,
    message, alert_start, alert_end, duration_seconds, is_resolved, notification_sent
) VALUES
(1, 1, 'warning', 82.5, 80.0, 'CPU使用率超过警告阈值: 82.5% > 80.0%',
 NOW() - INTERVAL 2 HOUR, NOW() - INTERVAL 1 HOUR, 3600, 1, 1),
(3, 1, 'warning', 88.2, 90.0, '计划缓存命中率低于警告阈值: 88.2% < 90.0%',
 NOW() - INTERVAL 4 HOUR, NOW() - INTERVAL 3 HOUR, 3600, 1, 1),
(4, 1, 'critical', 55, 50, 'RPC队列长度超过严重阈值: 55 > 50',
 NOW() - INTERVAL 30 MINUTE, NULL, NULL, 0, 1);

-- 提交事务
COMMIT;
