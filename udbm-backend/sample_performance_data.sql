-- 性能调优模块示例数据
-- 注意：假设数据库实例ID为1（UDBM PostgreSQL Database）

-- 插入慢查询示例数据
INSERT INTO udbm.slow_queries (
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

(1, 'SELECT o.*, u.name, u.email FROM orders o JOIN users u ON o.user_id = u.id WHERE o.status IN (''pending'', ''processing'') AND o.created_at >= CURRENT_DATE - INTERVAL ''7 days''',
 'jkl012mno345', 1.67, 0.23, 456, 15000, 'api@192.168.1.150', 'SELECT', 'active',
 '{"complexity_score": 65, "efficiency_score": 60, "bottlenecks": ["suboptimal_join"]}',
 '["为 orders.status 创建复合索引", "优化日期范围查询"]'),

(1, 'DELETE FROM logs WHERE created_at < CURRENT_DATE - INTERVAL ''90 days''',
 'mno345pqr678', 5.23, 1.45, 12500, 12500, 'cleanup@localhost', 'DELETE', 'resolved',
 '{"complexity_score": 30, "efficiency_score": 25, "bottlenecks": ["full_table_scan", "large_dataset"]}',
 '["为 logs.created_at 创建索引", "分批删除数据"]');

-- 插入索引建议示例数据
INSERT INTO udbm.index_suggestions (
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
INSERT INTO udbm.tuning_tasks (
    database_id, task_type, task_name, description, task_config,
    execution_sql, status, priority, related_suggestion_id
) VALUES
(1, 'index_creation', '为表 users 创建索引', 
 '创建 users.created_at 索引以优化用户查询性能，预计提升70-80%查询性能',
 '{"table_name": "users", "columns": ["created_at"], "index_type": "btree", "index_name": "idx_users_created_at", "reason": "频繁按创建时间查询", "estimated_improvement": "70-80%"}',
 'CREATE INDEX CONCURRENTLY idx_users_created_at ON users (created_at);',
 'pending', 5, 1),

(1, 'index_creation', '为表 products 创建索引',
 '创建 products.status 索引以优化商品状态查询，预计提升60-75%查询性能',
 '{"table_name": "products", "columns": ["status"], "index_type": "btree", "index_name": "idx_products_status", "reason": "商品状态查询频繁", "estimated_improvement": "60-75%"}',
 'CREATE INDEX CONCURRENTLY idx_products_status ON products (status);',
 'pending', 4, 2),

(1, 'index_creation', '为表 orders 创建复合索引',
 '创建 orders 表复合索引以优化用户订单查询，预计提升65-85%查询性能',
 '{"table_name": "orders", "columns": ["user_id", "created_at"], "index_type": "btree", "index_name": "idx_orders_user_created", "reason": "用户订单查询优化", "estimated_improvement": "65-85%"}',
 'CREATE INDEX CONCURRENTLY idx_orders_user_created ON orders (user_id, created_at);',
 'pending', 5, 3),

(1, 'index_creation', '为表 inventory 创建索引',
 '创建 inventory.product_id 索引以优化库存更新操作，预计提升80-90%更新性能',
 '{"table_name": "inventory", "columns": ["product_id"], "index_type": "btree", "index_name": "idx_inventory_product_id", "reason": "库存更新优化", "estimated_improvement": "80-90%"}',
 'CREATE INDEX CONCURRENTLY idx_inventory_product_id ON inventory (product_id);',
 'running', 5, 4),

(1, 'vacuum', 'VACUUM 表 logs',
 '执行 VACUUM 操作清理表 logs 的死元组，优化存储空间和查询性能',
 '{"table_name": "logs", "vacuum_type": "VACUUM", "estimated_duration": "30-300秒"}',
 'VACUUM logs;',
 'completed', 3, NULL),

(1, 'analyze', '分析表 users 统计信息',
 '更新表 users 的统计信息以优化查询计划，提升查询优化器决策准确性',
 '{"table_name": "users", "analyze_type": "ANALYZE", "estimated_duration": "10-60秒"}',
 'ANALYZE users;',
 'completed', 3, NULL),

(1, 'query_rewrite', '查询重写优化',
 '重写低效查询以提升性能，优化JOIN操作和WHERE条件',
 '{"original_query": "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > ''2024-01-01''", "rewritten_query": "SELECT u.id, u.name, o.id as order_id, o.total FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > ''2024-01-01'' AND u.status = ''active''", "analysis": {"original_complexity": "high", "rewritten_complexity": "medium", "estimated_improvement": "40-50%"}}',
 NULL,
 'pending', 2, NULL),

(1, 'vacuum', 'VACUUM ANALYZE 表 products',
 '执行 VACUUM ANALYZE 操作清理表 products 并更新统计信息',
 '{"table_name": "products", "vacuum_type": "VACUUM ANALYZE", "estimated_duration": "60-180秒"}',
 'VACUUM ANALYZE products;',
 'failed', 4, NULL);

-- 插入性能指标示例数据
INSERT INTO udbm.performance_metrics (
    database_id, metric_type, metric_name, metric_value, unit, tags, metric_metadata
) VALUES
(1, 'cpu', 'cpu_usage', 65.5, '%', '{"host": "db-server-01", "instance": "postgresql"}', '{"source": "system_monitor", "collection_method": "psutil"}'),
(1, 'memory', 'memory_usage', 78.2, '%', '{"host": "db-server-01", "instance": "postgresql"}', '{"source": "system_monitor", "total_memory": "16GB"}'),
(1, 'io', 'disk_read_iops', 1250.8, 'iops', '{"device": "/dev/sda1", "mount": "/var/lib/postgresql"}', '{"source": "iostat", "read_latency": "2.5ms"}'),
(1, 'io', 'disk_write_iops', 890.3, 'iops', '{"device": "/dev/sda1", "mount": "/var/lib/postgresql"}', '{"source": "iostat", "write_latency": "3.2ms"}'),
(1, 'connections', 'active_connections', 45, 'count', '{"max_connections": "100"}', '{"source": "pg_stat_activity", "idle_connections": 12}'),
(1, 'connections', 'waiting_connections', 3, 'count', '{"timeout_threshold": "30s"}', '{"source": "pg_stat_activity", "longest_wait": "15s"}'),
(1, 'throughput', 'queries_per_second', 234.7, 'qps', '{"query_type": "all"}', '{"source": "pg_stat_statements", "peak_qps": 456.2}'),
(1, 'throughput', 'transactions_per_second', 89.3, 'tps', '{"transaction_type": "all"}', '{"source": "pg_stat_database", "commit_ratio": 0.98}');

-- 插入执行计划示例数据
INSERT INTO udbm.execution_plans (
    database_id, query_text, query_hash, plan_json, plan_text,
    cost_estimate, rows_estimate, actual_rows, execution_time,
    analysis_result, optimization_suggestions
) VALUES
(1, 'SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > ''2024-01-01''',
 'abc123def456',
 '{"Plan": {"Node Type": "Hash Join", "Total Cost": 1234.56, "Plan Rows": 1250, "Actual Rows": 1200, "Plans": [{"Node Type": "Seq Scan", "Relation Name": "users"}, {"Node Type": "Hash", "Plans": [{"Node Type": "Seq Scan", "Relation Name": "orders"}]}]}}',
 'Hash Join  (cost=456.78..1234.56 rows=1250 width=128) (actual time=12.345..2450.123 rows=1200 loops=1)\n  Hash Cond: (o.user_id = u.id)\n  ->  Seq Scan on orders o  (cost=0.00..567.89 rows=15000 width=64)\n  ->  Hash  (cost=234.56..234.56 rows=5000 width=64)\n        ->  Seq Scan on users u  (cost=0.00..234.56 rows=5000 width=64)\n              Filter: (created_at > ''2024-01-01''::date)',
 1234.56, 1250, 1200, 2.45,
 '{"performance_score": 35, "bottlenecks": ["seq_scan_users", "seq_scan_orders", "missing_indexes"], "cost_analysis": {"estimated": 1234.56, "actual": 2450.123, "variance": "99%"}}',
 '["为 users.created_at 创建索引", "为 orders.user_id 创建索引", "考虑使用 LIMIT 限制结果集"]'),

(1, 'SELECT COUNT(*) FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.status = ''active''',
 'def456ghi789',
 '{"Plan": {"Node Type": "Aggregate", "Total Cost": 678.90, "Plan Rows": 1, "Actual Rows": 1, "Plans": [{"Node Type": "Hash Left Join", "Plans": [{"Node Type": "Seq Scan", "Relation Name": "products"}, {"Node Type": "Hash", "Plans": [{"Node Type": "Seq Scan", "Relation Name": "categories"}]}]}]}}',
 'Aggregate  (cost=650.00..678.90 rows=1 width=8) (actual time=1890.123..1890.124 rows=1 loops=1)\n  ->  Hash Left Join  (cost=123.45..650.00 rows=5000 width=0)\n        Hash Cond: (p.category_id = c.id)\n        ->  Seq Scan on products p  (cost=0.00..456.78 rows=5000 width=4)\n              Filter: (status = ''active'')\n        ->  Hash  (cost=89.12..89.12 rows=1500 width=4)\n              ->  Seq Scan on categories c  (cost=0.00..89.12 rows=1500 width=4)',
 678.90, 1, 1, 1.89,
 '{"performance_score": 45, "bottlenecks": ["seq_scan_products", "missing_index_status"], "cost_analysis": {"estimated": 678.90, "actual": 1890.123, "variance": "178%"}}',
 '["为 products.status 创建索引", "考虑创建部分索引仅包含 active 状态"]');

-- 插入系统诊断示例数据
INSERT INTO udbm.system_diagnoses (
    database_id, diagnosis_type, overall_score, diagnosis_result,
    recommendations, performance_score, security_score, maintenance_score
) VALUES
(1, 'full', 72.5,
 '{"summary": "数据库整体运行状况良好，但存在一些性能优化空间", "issues": [{"category": "performance", "severity": "medium", "description": "检测到5个缺失索引", "impact": "查询性能下降30-50%"}, {"category": "maintenance", "severity": "low", "description": "部分表需要VACUUM维护", "impact": "存储空间浪费15%"}, {"category": "security", "severity": "low", "description": "建议启用查询日志审计", "impact": "安全监控不完整"}], "metrics": {"slow_queries_count": 5, "missing_indexes_count": 6, "bloated_tables_count": 2, "connection_utilization": 45}}',
 '["创建缺失的索引以提升查询性能", "执行VACUUM维护清理死元组", "启用查询日志和审计功能", "优化数据库配置参数", "建立定期维护计划"]',
 68.5, 82.0, 67.0),

(1, 'quick', 75.8,
 '{"summary": "快速检查显示系统运行正常，性能指标在可接受范围内", "issues": [{"category": "performance", "severity": "low", "description": "CPU使用率略高", "impact": "响应时间可能受影响"}, {"category": "connections", "severity": "low", "description": "连接数使用率45%", "impact": "连接池需要监控"}], "metrics": {"cpu_usage": 65.5, "memory_usage": 78.2, "active_connections": 45, "qps": 234.7}}',
 '["监控CPU使用率趋势", "优化高频查询", "考虑连接池配置调整"]',
 75.2, 85.5, 70.0);

-- 更新创建时间为不同时间点，模拟真实的时间分布
UPDATE udbm.slow_queries SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 days' WHERE id = 1;
UPDATE udbm.slow_queries SET created_at = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE id = 2;
UPDATE udbm.slow_queries SET created_at = CURRENT_TIMESTAMP - INTERVAL '12 hours' WHERE id = 3;
UPDATE udbm.slow_queries SET created_at = CURRENT_TIMESTAMP - INTERVAL '6 hours' WHERE id = 4;
UPDATE udbm.slow_queries SET created_at = CURRENT_TIMESTAMP - INTERVAL '3 hours' WHERE id = 5;

UPDATE udbm.index_suggestions SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 days' WHERE id = 1;
UPDATE udbm.index_suggestions SET created_at = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE id = 2;
UPDATE udbm.index_suggestions SET created_at = CURRENT_TIMESTAMP - INTERVAL '18 hours' WHERE id = 3;
UPDATE udbm.index_suggestions SET created_at = CURRENT_TIMESTAMP - INTERVAL '12 hours' WHERE id = 4;
UPDATE udbm.index_suggestions SET created_at = CURRENT_TIMESTAMP - INTERVAL '8 hours' WHERE id = 5;
UPDATE udbm.index_suggestions SET created_at = CURRENT_TIMESTAMP - INTERVAL '4 hours' WHERE id = 6;

UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 days' WHERE id = 1;
UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE id = 2;
UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '18 hours' WHERE id = 3;
UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '12 hours' WHERE id = 4;
UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '8 hours', completed_at = CURRENT_TIMESTAMP - INTERVAL '7 hours' WHERE id = 5;
UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '6 hours', completed_at = CURRENT_TIMESTAMP - INTERVAL '5 hours' WHERE id = 6;
UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '4 hours' WHERE id = 7;
UPDATE udbm.tuning_tasks SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 hours', started_at = CURRENT_TIMESTAMP - INTERVAL '1 hour', completed_at = CURRENT_TIMESTAMP - INTERVAL '30 minutes' WHERE id = 8;

UPDATE udbm.performance_metrics SET timestamp = CURRENT_TIMESTAMP - INTERVAL '5 minutes' WHERE id <= 4;
UPDATE udbm.performance_metrics SET timestamp = CURRENT_TIMESTAMP - INTERVAL '10 minutes' WHERE id > 4;

UPDATE udbm.execution_plans SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 days', timestamp = CURRENT_TIMESTAMP - INTERVAL '2 days' WHERE id = 1;
UPDATE udbm.execution_plans SET created_at = CURRENT_TIMESTAMP - INTERVAL '1 day', timestamp = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE id = 2;

UPDATE udbm.system_diagnoses SET created_at = CURRENT_TIMESTAMP - INTERVAL '1 day', timestamp = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE id = 1;
UPDATE udbm.system_diagnoses SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 hours', timestamp = CURRENT_TIMESTAMP - INTERVAL '2 hours' WHERE id = 2;
