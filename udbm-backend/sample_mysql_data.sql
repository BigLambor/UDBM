-- UDBM MySQL 示例数据脚本
-- 为测试和演示生成示例数据

USE udbm_mysql_demo;

-- 生成测试数据（直接插入，不依赖存储过程）
-- 生成产品数据
INSERT INTO products (name, description, price, category_id, stock_quantity, status)
SELECT 
    CONCAT('产品_', n.n) as name,
    CONCAT('这是产品', n.n, '的详细描述') as description,
    ROUND(RAND() * 999 + 1, 2) as price,
    FLOOR(RAND() * 8) + 1 as category_id,
    FLOOR(RAND() * 100) as stock_quantity,
    CASE 
        WHEN RAND() < 0.8 THEN 'active'
        WHEN RAND() < 0.95 THEN 'inactive'
        ELSE 'discontinued'
    END as status
FROM (
    SELECT 1 as n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
    UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25
    UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
    UNION SELECT 31 UNION SELECT 32 UNION SELECT 33 UNION SELECT 34 UNION SELECT 35
    UNION SELECT 36 UNION SELECT 37 UNION SELECT 38 UNION SELECT 39 UNION SELECT 40
    UNION SELECT 41 UNION SELECT 42 UNION SELECT 43 UNION SELECT 44 UNION SELECT 45
    UNION SELECT 46 UNION SELECT 47 UNION SELECT 48 UNION SELECT 49 UNION SELECT 50
    UNION SELECT 51 UNION SELECT 52 UNION SELECT 53 UNION SELECT 54 UNION SELECT 55
    UNION SELECT 56 UNION SELECT 57 UNION SELECT 58 UNION SELECT 59 UNION SELECT 60
    UNION SELECT 61 UNION SELECT 62 UNION SELECT 63 UNION SELECT 64 UNION SELECT 65
    UNION SELECT 66 UNION SELECT 67 UNION SELECT 68 UNION SELECT 69 UNION SELECT 70
    UNION SELECT 71 UNION SELECT 72 UNION SELECT 73 UNION SELECT 74 UNION SELECT 75
    UNION SELECT 76 UNION SELECT 77 UNION SELECT 78 UNION SELECT 79 UNION SELECT 80
    UNION SELECT 81 UNION SELECT 82 UNION SELECT 83 UNION SELECT 84 UNION SELECT 85
    UNION SELECT 86 UNION SELECT 87 UNION SELECT 88 UNION SELECT 89 UNION SELECT 90
    UNION SELECT 91 UNION SELECT 92 UNION SELECT 93 UNION SELECT 94 UNION SELECT 95
    UNION SELECT 96 UNION SELECT 97 UNION SELECT 98 UNION SELECT 99 UNION SELECT 100
) n;

-- 生成一些订单详情数据
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
SELECT 
    o.id as order_id,
    p.id as product_id,
    FLOOR(RAND() * 5) + 1 as quantity,
    p.price as unit_price,
    (FLOOR(RAND() * 5) + 1) * p.price as total_price
FROM orders o
CROSS JOIN products p
WHERE RAND() < 0.3  -- 30% 的概率生成订单项
LIMIT 500;

-- 生成活动日志数据
INSERT INTO activity_logs (user_id, action, resource_type, resource_id, details, ip_address, user_agent)
SELECT 
    u.id as user_id,
    CASE FLOOR(RAND() * 6)
        WHEN 0 THEN 'login'
        WHEN 1 THEN 'logout'
        WHEN 2 THEN 'create_order'
        WHEN 3 THEN 'update_profile'
        WHEN 4 THEN 'view_product'
        ELSE 'search'
    END as action,
    CASE FLOOR(RAND() * 4)
        WHEN 0 THEN 'user'
        WHEN 1 THEN 'product'
        WHEN 2 THEN 'order'
        ELSE 'category'
    END as resource_type,
    FLOOR(RAND() * 100) + 1 as resource_id,
    JSON_OBJECT(
        'timestamp', NOW(),
        'session_id', UUID(),
        'success', RAND() > 0.1,
        'duration_ms', FLOOR(RAND() * 5000) + 100
    ) as details,
    CONCAT(
        FLOOR(RAND() * 255) + 1, '.', 
        FLOOR(RAND() * 255) + 1, '.', 
        FLOOR(RAND() * 255) + 1, '.', 
        FLOOR(RAND() * 255) + 1
    ) as ip_address,
    CASE FLOOR(RAND() * 4)
        WHEN 0 THEN 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        WHEN 1 THEN 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        WHEN 2 THEN 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ELSE 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)'
    END as user_agent
FROM users u
CROSS JOIN (
    SELECT 1 as n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
) numbers
WHERE RAND() < 0.8;

-- 更新一些订单的总金额（基于订单项）
UPDATE orders o
SET total_amount = (
    SELECT COALESCE(SUM(oi.total_price), 0)
    FROM order_items oi
    WHERE oi.order_id = o.id
)
WHERE EXISTS (
    SELECT 1 
    FROM order_items oi2 
    WHERE oi2.order_id = o.id
);

-- 创建一些索引来测试性能优化建议
-- （故意创建一些可能不必要的索引）
CREATE INDEX idx_products_name_price ON products(name, price);
CREATE INDEX idx_orders_created_status ON orders(created_at, status);
CREATE INDEX idx_performance_test_complex ON performance_test(test_name, status, execution_time, created_at);

-- 创建一个存储过程用于模拟慢查询
DELIMITER //

CREATE PROCEDURE SimulateSlowQuery(IN seconds INT)
BEGIN
    DECLARE start_time TIMESTAMP DEFAULT NOW();
    DECLARE current_ts TIMESTAMP;
    
    -- 模拟一个复杂的查询，会执行指定秒数
    slow_loop: LOOP
        SET current_ts = NOW();
        
        -- 执行一些复杂计算
        SELECT COUNT(*) INTO @dummy_count
        FROM performance_test pt1
        CROSS JOIN performance_test pt2
        WHERE pt1.id < pt2.id
            AND pt1.execution_time > pt2.execution_time
            AND pt1.test_name LIKE '%测试%'
        LIMIT 1;
        
        -- 检查是否已经运行了足够长的时间
        IF TIMESTAMPDIFF(SECOND, start_time, current_ts) >= seconds THEN
            LEAVE slow_loop;
        END IF;
    END LOOP;
    
    SELECT CONCAT('慢查询模拟完成，运行了 ', seconds, ' 秒') as result;
END //

DELIMITER ;

-- 创建一个函数用于生成随机数据
DELIMITER //

CREATE FUNCTION GenerateRandomString(length INT) RETURNS VARCHAR(255)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE result VARCHAR(255) DEFAULT '';
    DECLARE chars VARCHAR(62) DEFAULT 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    DECLARE i INT DEFAULT 1;
    
    WHILE i <= length DO
        SET result = CONCAT(result, SUBSTRING(chars, FLOOR(RAND() * 62) + 1, 1));
        SET i = i + 1;
    END WHILE;
    
    RETURN result;
END //

DELIMITER ;

-- 插入一些大文本数据用于测试
INSERT INTO performance_test (test_name, test_data, execution_time, memory_usage, cpu_usage, status, metadata)
SELECT 
    CONCAT('大数据测试_', ROW_NUMBER() OVER (ORDER BY RAND())) as test_name,
    REPEAT(GenerateRandomString(100), 50) as test_data,
    ROUND(RAND() * 30 + 0.1, 6) as execution_time,
    FLOOR(RAND() * 2048) + 512 as memory_usage,
    ROUND(RAND() * 100, 2) as cpu_usage,
    'completed' as status,
    JSON_OBJECT(
        'data_size', 'large',
        'test_category', 'stress_test',
        'complexity', 'high',
        'generated_at', NOW()
    ) as metadata
FROM (
    SELECT 1 as n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
) numbers;

-- 创建一些分区表用于测试（如果支持）
-- CREATE TABLE IF NOT EXISTS partitioned_logs (
--     id INT AUTO_INCREMENT,
--     log_date DATE NOT NULL,
--     log_level ENUM('DEBUG', 'INFO', 'WARN', 'ERROR') DEFAULT 'INFO',
--     message TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     PRIMARY KEY (id, log_date),
--     INDEX idx_log_level (log_level),
--     INDEX idx_created_at (created_at)
-- ) PARTITION BY RANGE (YEAR(log_date)) (
--     PARTITION p2023 VALUES LESS THAN (2024),
--     PARTITION p2024 VALUES LESS THAN (2025),
--     PARTITION p2025 VALUES LESS THAN (2026),
--     PARTITION p_future VALUES LESS THAN MAXVALUE
-- );

-- 显示一些统计信息
SELECT '=== MySQL测试数据统计 ===' as info;
SELECT 'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'activity_logs', COUNT(*) FROM activity_logs
UNION ALL
SELECT 'performance_test', COUNT(*) FROM performance_test;

-- 显示数据库大小信息
SELECT 
    table_schema as '数据库',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as '大小(MB)',
    COUNT(*) as '表数量'
FROM information_schema.tables 
WHERE table_schema = 'udbm_mysql_demo'
GROUP BY table_schema;

SELECT 'MySQL示例数据生成完成！' as message;
SELECT 'UDBM MySQL测试环境数据已就绪，可以进行性能测试和监控' as status;
