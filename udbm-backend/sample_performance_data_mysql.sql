-- MySQL 性能调优模块示例数据
-- 注意：假设数据库实例ID为1（UDBM MySQL Demo Database）

USE udbm_mysql_demo;

-- 插入慢查询示例数据
INSERT INTO slow_queries (
    database_id, query_text, query_hash, execution_time, lock_time, 
    rows_sent, rows_examined, user_host, sql_command, status,
    analysis_result, optimization_suggestions
) VALUES
(1, 'SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > ''2024-01-01'' ORDER BY o.created_at DESC', 
 'abc123def456', 2.45, 0.12, 1250, 50000, 'app@192.168.1.100', 'SELECT', 'active',
 '{"complexity_score": 75, "efficiency_score": 45, "bottlenecks": ["missing_index", "full_table_scan"]}',
 '["为 users.created_at 创建索引", "为 orders.user_id 创建索引", "限制返回字段"]'),

(1, 'SELECT COUNT(*) FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.status = ''active''',
 'def456ghi789', 1.89, 0.05, 1, 25000, 'admin@localhost', 'SELECT', 'active',
 '{"complexity_score": 60, "efficiency_score": 55, "bottlenecks": ["missing_index"]}',
 '["为 products.status 创建索引", "考虑使用覆盖索引"]'),

(1, 'UPDATE inventory SET quantity = quantity - 1 WHERE product_id = 12345 AND quantity > 0',
 'ghi789jkl012', 3.12, 0.89, 1, 1, 'app@192.168.1.200', 'UPDATE', 'active',
 '{"complexity_score": 40, "efficiency_score": 30, "bottlenecks": ["lock_contention", "missing_index"]}',
 '["为 inventory.product_id 创建唯一索引", "优化锁策略"]'),

(1, 'SELECT o.*, u.name, u.email FROM orders o JOIN users u ON o.user_id = u.id WHERE o.status IN (''pending'', ''processing'') AND o.created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)',
 'jkl012mno345', 1.67, 0.23, 456, 15000, 'api@192.168.1.150', 'SELECT', 'active',
 '{"complexity_score": 65, "efficiency_score": 60, "bottlenecks": ["suboptimal_join"]}',
 '["为 orders.status 创建复合索引", "优化日期范围查询"]'),

(1, 'DELETE FROM logs WHERE created_at < DATE_SUB(CURDATE(), INTERVAL 90 DAY)',
 'mno345pqr678', 5.23, 1.45, 12500, 12500, 'cleanup@localhost', 'DELETE', 'resolved',
 '{"complexity_score": 30, "efficiency_score": 25, "bottlenecks": ["full_table_scan", "large_dataset"]}',
 '["为 logs.created_at 创建索引", "分批删除数据"]');

-- 插入索引建议示例数据
INSERT INTO index_suggestions (
    database_id, table_name, column_names, index_type, suggestion_type,
    reason, impact_score, estimated_improvement, status, related_query_ids
) VALUES
(1, 'users', '["created_at"]', 'btree', 'missing',
 '检测到频繁按创建时间查询用户，但缺少相应索引。查询平均执行时间2.45秒，影响用户体验。',
 85.5, '预计查询性能提升70-80%，响应时间减少至0.3秒以内', 'pending', '[1, 4]'),

(1, 'products', '["status"]', 'btree', 'missing',
 '产品状态查询频繁，缺少索引导致全表扫描。影响商品列表和统计查询性能。',
 78.2, '预计查询性能提升60-75%，特别是商品筛选功能', 'pending', '[2]'),

(1, 'orders', '["user_id", "created_at"]', 'btree', 'missing',
 '用户订单查询和时间范围查询频繁，需要复合索引优化。当前查询涉及大量行扫描。',
 82.1, '预计查询性能提升65-85%，用户订单页面加载速度显著提升', 'pending', '[1, 4]'),

(1, 'inventory', '["product_id"]', 'btree', 'missing',
 '库存更新操作频繁，产品ID查询缺少索引，导致锁等待时间过长。',
 88.7, '预计更新性能提升80-90%，减少锁等待时间', 'pending', '[3]'),

(1, 'logs', '["created_at"]', 'btree', 'missing',
 '日志清理任务需要按时间范围删除，缺少时间索引导致全表扫描。',
 72.3, '预计清理任务性能提升85-95%，减少系统维护时间', 'applied', '[5]'),

(1, 'orders', '["status", "created_at"]', 'btree', 'missing',
 '订单状态和时间复合查询频繁，建议创建复合索引优化查询性能。',
 79.8, '预计订单管理查询性能提升60-70%', 'pending', '[4]');

-- 插入调优任务示例数据
INSERT INTO tuning_tasks (
    database_id, task_type, task_name, description, task_config,
    execution_sql, status, priority, related_suggestion_id
) VALUES
(1, 'index_creation', '为表 users 创建索引', 
 '创建 users.created_at 索引以优化用户查询性能，预计提升70-80%查询性能',
 '{"table_name": "users", "columns": ["created_at"], "index_type": "btree", "index_name": "idx_users_created_at", "reason": "频繁按创建时间查询", "estimated_improvement": "70-80%"}',
 'CREATE INDEX idx_users_created_at ON users (created_at);',
 'pending', 5, 1),

(1, 'index_creation', '为表 products 创建索引',
 '创建 products.status 索引以优化商品状态查询，预计提升60-75%查询性能',
 '{"table_name": "products", "columns": ["status"], "index_type": "btree", "index_name": "idx_products_status", "reason": "商品状态查询频繁", "estimated_improvement": "60-75%"}',
 'CREATE INDEX idx_products_status ON products (status);',
 'pending', 4, 2),

(1, 'index_creation', '为表 orders 创建复合索引',
 '创建 orders 表复合索引以优化用户订单查询，预计提升65-85%查询性能',
 '{"table_name": "orders", "columns": ["user_id", "created_at"], "index_type": "btree", "index_name": "idx_orders_user_created", "reason": "用户订单查询优化", "estimated_improvement": "65-85%"}',
 'CREATE INDEX idx_orders_user_created ON orders (user_id, created_at);',
 'pending', 5, 3),

(1, 'index_creation', '为表 inventory 创建索引',
 '创建 inventory.product_id 索引以优化库存更新操作，预计提升80-90%更新性能',
 '{"table_name": "inventory", "columns": ["product_id"], "index_type": "btree", "index_name": "idx_inventory_product_id", "reason": "库存更新优化", "estimated_improvement": "80-90%"}',
 'CREATE INDEX idx_inventory_product_id ON inventory (product_id);',
 'running', 5, 4),

(1, 'analyze', '分析表 users 统计信息',
 '更新表 users 的统计信息以优化查询计划，提升查询优化器决策准确性',
 '{"table_name": "users", "analyze_type": "ANALYZE", "estimated_duration": "10-60秒"}',
 'ANALYZE TABLE users;',
 'completed', 3, NULL),

(1, 'query_rewrite', '查询重写优化',
 '重写低效查询以提升性能，优化JOIN操作和WHERE条件',
 '{"original_query": "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > ''2024-01-01''", "rewritten_query": "SELECT u.id, u.name, o.id as order_id, o.total FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > ''2024-01-01'' AND u.status = ''active''", "analysis": {"original_complexity": "high", "rewritten_complexity": "medium", "estimated_improvement": "40-50%"}}',
 NULL,
 'pending', 2, NULL),

(1, 'analyze', '分析表 products 统计信息',
 '更新表 products 的统计信息以优化查询计划',
 '{"table_name": "products", "analyze_type": "ANALYZE", "estimated_duration": "30-120秒"}',
 'ANALYZE TABLE products;',
 'failed', 4, NULL);

-- 插入性能指标示例数据
INSERT INTO performance_metrics (
    database_id, metric_type, metric_name, metric_value, unit, tags, metric_metadata
) VALUES
(1, 'cpu', 'cpu_usage', 65.5, '%', '{"host": "db-server-01", "instance": "mysql"}', '{"source": "system_monitor", "collection_method": "psutil"}'),
(1, 'memory', 'memory_usage', 78.2, '%', '{"host": "db-server-01", "instance": "mysql"}', '{"source": "system_monitor", "total_memory": "16GB"}'),
(1, 'io', 'disk_read_iops', 1250.8, 'iops', '{"device": "/dev/sda1", "mount": "/var/lib/mysql"}', '{"source": "iostat", "read_latency": "2.5ms"}'),
(1, 'io', 'disk_write_iops', 890.3, 'iops', '{"device": "/dev/sda1", "mount": "/var/lib/mysql"}', '{"source": "iostat", "write_latency": "3.2ms"}'),
(1, 'connections', 'active_connections', 45, 'count', '{"max_connections": "100"}', '{"source": "performance_schema", "idle_connections": 12}'),
(1, 'connections', 'waiting_connections', 3, 'count', '{"timeout_threshold": "30s"}', '{"source": "performance_schema", "longest_wait": "15s"}'),
(1, 'throughput', 'queries_per_second', 234.7, 'qps', '{"query_type": "all"}', '{"source": "performance_schema", "peak_qps": 456.2}'),
(1, 'throughput', 'transactions_per_second', 89.3, 'tps', '{"transaction_type": "all"}', '{"source": "performance_schema", "commit_ratio": 0.98}'),
(1, 'mysql', 'innodb_buffer_pool_hit_ratio', 95.2, '%', '{"engine": "innodb"}', '{"source": "performance_schema", "buffer_pool_size": "1GB"}'),
(1, 'mysql', 'key_buffer_hit_ratio', 98.5, '%', '{"engine": "myisam"}', '{"source": "performance_schema", "key_buffer_size": "256MB"}'),
(1, 'mysql', 'query_cache_hit_ratio', 85.3, '%', '{"cache_type": "query"}', '{"source": "performance_schema", "query_cache_size": "128MB"}'),
(1, 'mysql', 'table_locks_waited', 125, 'count', '{"lock_type": "table"}', '{"source": "performance_schema", "lock_wait_time": "0.5s"}');

-- 插入执行计划示例数据
INSERT INTO execution_plans (
    database_id, query_text, query_hash, plan_json, plan_text,
    cost_estimate, rows_estimate, actual_rows, execution_time,
    analysis_result, optimization_suggestions
) VALUES
(1, 'SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > ''2024-01-01''',
 'abc123def456',
 '{"query_block": {"select_id": 1, "cost_info": {"query_cost": "1234.56"}, "nested_loop": [{"table": {"table_name": "u", "access_type": "ALL", "rows_examined_per_scan": 5000, "rows_produced_per_join": 1250}}, {"table": {"table_name": "o", "access_type": "ref", "key": "user_id", "rows_examined_per_scan": 3}}]}}',
 '-> Nested loop inner join  (cost=1234.56 rows=1250) (actual time=12.345..2450.123 rows=1200 loops=1)
    -> Table scan on u  (cost=234.56 rows=5000) (actual time=0.123..45.678 rows=5000 loops=1)
    -> Index lookup on o using user_id (user_id=u.id)  (cost=0.25 rows=3) (actual time=0.001..0.456 rows=3 loops=5000)',
 1234.56, 1250, 1200, 2.45,
 '{"performance_score": 35, "bottlenecks": ["table_scan_users", "missing_indexes"], "cost_analysis": {"estimated": 1234.56, "actual": 2450.123, "variance": "99%"}}',
 '["为 users.created_at 创建索引", "为 orders.user_id 创建索引", "考虑使用 LIMIT 限制结果集"]'),

(1, 'SELECT COUNT(*) FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.status = ''active''',
 'def456ghi789',
 '{"query_block": {"select_id": 1, "cost_info": {"query_cost": "678.90"}, "grouping_operation": {"using_temporary_table": true, "using_filesort": false, "nested_loop": [{"table": {"table_name": "p", "access_type": "ALL", "rows_examined_per_scan": 25000}}, {"table": {"table_name": "c", "access_type": "eq_ref", "key": "PRIMARY", "rows_examined_per_scan": 1}}]}}}',
 '-> Aggregate: count(0)  (cost=678.90 rows=1) (actual time=1890.123..1890.124 rows=1 loops=1)
    -> Nested loop left join  (cost=650.00 rows=5000) (actual time=0.123..1890.123 rows=5000 loops=1)
        -> Table scan on p  (cost=456.78 rows=5000) (actual time=0.123..45.678 rows=5000 loops=1)
        -> Single-row index lookup on c using PRIMARY (id=p.category_id)  (cost=0.25 rows=1) (actual time=0.001..0.123 rows=1 loops=5000)',
 678.90, 1, 1, 1.89,
 '{"performance_score": 45, "bottlenecks": ["table_scan_products", "missing_index_status"], "cost_analysis": {"estimated": 678.90, "actual": 1890.123, "variance": "178%"}}',
 '["为 products.status 创建索引", "考虑创建部分索引仅包含 active 状态"]');

-- 插入系统诊断示例数据
INSERT INTO system_diagnoses (
    database_id, diagnosis_type, overall_score, diagnosis_result,
    recommendations, performance_score, security_score, maintenance_score
) VALUES
(1, 'full', 72.5,
 '{"summary": "数据库整体运行状况良好，但存在一些性能优化空间", "issues": [{"category": "performance", "severity": "medium", "description": "检测到5个缺失索引", "impact": "查询性能下降30-50%"}, {"category": "maintenance", "severity": "low", "description": "部分表需要OPTIMIZE TABLE维护", "impact": "存储空间浪费15%"}, {"category": "security", "severity": "low", "description": "建议启用查询日志审计", "impact": "安全监控不完整"}], "metrics": {"slow_queries_count": 5, "missing_indexes_count": 6, "fragmented_tables_count": 2, "connection_utilization": 45}}',
 '["创建缺失的索引以提升查询性能", "执行OPTIMIZE TABLE维护清理碎片", "启用查询日志和审计功能", "优化MySQL配置参数", "建立定期维护计划"]',
 68.5, 82.0, 67.0),

(1, 'quick', 75.8,
 '{"summary": "快速检查显示系统运行正常，性能指标在可接受范围内", "issues": [{"category": "performance", "severity": "low", "description": "CPU使用率略高", "impact": "响应时间可能受影响"}, {"category": "connections", "severity": "low", "description": "连接数使用率45%", "impact": "连接池需要监控"}], "metrics": {"cpu_usage": 65.5, "memory_usage": 78.2, "active_connections": 45, "qps": 234.7}}',
 '["监控CPU使用率趋势", "优化高频查询", "考虑连接池配置调整"]',
 75.2, 85.5, 70.0);

-- 更新创建时间为不同时间点，模拟真实的时间分布
UPDATE slow_queries SET created_at = DATE_SUB(NOW(), INTERVAL 2 DAY) WHERE id = 1;
UPDATE slow_queries SET created_at = DATE_SUB(NOW(), INTERVAL 1 DAY) WHERE id = 2;
UPDATE slow_queries SET created_at = DATE_SUB(NOW(), INTERVAL 12 HOUR) WHERE id = 3;
UPDATE slow_queries SET created_at = DATE_SUB(NOW(), INTERVAL 6 HOUR) WHERE id = 4;
UPDATE slow_queries SET created_at = DATE_SUB(NOW(), INTERVAL 3 HOUR) WHERE id = 5;

UPDATE index_suggestions SET created_at = DATE_SUB(NOW(), INTERVAL 2 DAY) WHERE id = 1;
UPDATE index_suggestions SET created_at = DATE_SUB(NOW(), INTERVAL 1 DAY) WHERE id = 2;
UPDATE index_suggestions SET created_at = DATE_SUB(NOW(), INTERVAL 18 HOUR) WHERE id = 3;
UPDATE index_suggestions SET created_at = DATE_SUB(NOW(), INTERVAL 12 HOUR) WHERE id = 4;
UPDATE index_suggestions SET created_at = DATE_SUB(NOW(), INTERVAL 8 HOUR) WHERE id = 5;
UPDATE index_suggestions SET created_at = DATE_SUB(NOW(), INTERVAL 4 HOUR) WHERE id = 6;

UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 2 DAY) WHERE id = 1;
UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 1 DAY) WHERE id = 2;
UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 18 HOUR) WHERE id = 3;
UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 12 HOUR) WHERE id = 4;
UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 8 HOUR), completed_at = DATE_SUB(NOW(), INTERVAL 7 HOUR) WHERE id = 5;
UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 6 HOUR), completed_at = DATE_SUB(NOW(), INTERVAL 5 HOUR) WHERE id = 6;
UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 4 HOUR) WHERE id = 7;
UPDATE tuning_tasks SET created_at = DATE_SUB(NOW(), INTERVAL 2 HOUR), started_at = DATE_SUB(NOW(), INTERVAL 1 HOUR), completed_at = DATE_SUB(NOW(), INTERVAL 30 MINUTE) WHERE id = 8;

UPDATE performance_metrics SET timestamp = DATE_SUB(NOW(), INTERVAL 5 MINUTE) WHERE id <= 4;
UPDATE performance_metrics SET timestamp = DATE_SUB(NOW(), INTERVAL 10 MINUTE) WHERE id > 4;

UPDATE execution_plans SET created_at = DATE_SUB(NOW(), INTERVAL 2 DAY), timestamp = DATE_SUB(NOW(), INTERVAL 2 DAY) WHERE id = 1;
UPDATE execution_plans SET created_at = DATE_SUB(NOW(), INTERVAL 1 DAY), timestamp = DATE_SUB(NOW(), INTERVAL 1 DAY) WHERE id = 2;

UPDATE system_diagnoses SET created_at = DATE_SUB(NOW(), INTERVAL 1 DAY), timestamp = DATE_SUB(NOW(), INTERVAL 1 DAY) WHERE id = 1;
UPDATE system_diagnoses SET created_at = DATE_SUB(NOW(), INTERVAL 2 HOUR), timestamp = DATE_SUB(NOW(), INTERVAL 2 HOUR) WHERE id = 2;

-- 显示数据统计信息
SELECT '=== MySQL性能调优数据统计 ===' as info;
SELECT 'slow_queries' as table_name, COUNT(*) as record_count FROM slow_queries
UNION ALL
SELECT 'index_suggestions', COUNT(*) FROM index_suggestions
UNION ALL
SELECT 'tuning_tasks', COUNT(*) FROM tuning_tasks
UNION ALL
SELECT 'performance_metrics', COUNT(*) FROM performance_metrics
UNION ALL
SELECT 'execution_plans', COUNT(*) FROM execution_plans
UNION ALL
SELECT 'system_diagnoses', COUNT(*) FROM system_diagnoses;

SELECT 'MySQL性能调优示例数据生成完成！' as message;
SELECT 'UDBM MySQL性能监控环境数据已就绪' as status;
