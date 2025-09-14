-- UDBM MySQL 数据库初始化脚本
-- 统一数据库管理平台 - MySQL测试数据库

-- 创建测试数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS udbm_mysql_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE udbm_mysql_demo;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    department VARCHAR(100),
    role ENUM('admin', 'dba', 'operator', 'viewer') DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_department (department),
    INDEX idx_role_active (role, is_active)
);

-- 创建产品表
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category_id INT,
    stock_quantity INT DEFAULT 0,
    status ENUM('active', 'inactive', 'discontinued') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_category (category_id),
    INDEX idx_status (status)
);

-- 创建分类表
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    parent_id INT,
    level INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_parent (parent_id),
    INDEX idx_level (level),
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    payment_status ENUM('unpaid', 'paid', 'refunded') DEFAULT 'unpaid',
    shipping_address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_order_number (order_number),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建订单详情表
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order (order_id),
    INDEX idx_product (product_id),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 创建日志表
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INT,
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 创建性能测试表（用于测试慢查询）
CREATE TABLE IF NOT EXISTS performance_test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL,
    test_data LONGTEXT,
    execution_time DECIMAL(10, 6),
    memory_usage INT,
    cpu_usage DECIMAL(5, 2),
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_test_name (test_name),
    INDEX idx_status (status),
    INDEX idx_execution_time (execution_time),
    INDEX idx_created_at (created_at)
);

-- 插入基础分类数据
INSERT INTO categories (name, description, parent_id, level) VALUES
('电子产品', '各种电子设备和配件', NULL, 1),
('服装', '男女服装和配饰', NULL, 1),
('家居用品', '家庭日用品和装饰', NULL, 1),
('图书', '各类书籍和教材', NULL, 1),
('手机', '智能手机和配件', 1, 2),
('电脑', '台式机和笔记本电脑', 1, 2),
('男装', '男性服装', 2, 2),
('女装', '女性服装', 2, 2)
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- 插入测试用户数据
INSERT INTO users (username, email, password_hash, full_name, department, role) VALUES
('admin', 'admin@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfLkIwWQXjZzQaO', '系统管理员', 'IT部门', 'admin'),
('dba_user', 'dba@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfLkIwWQXjZzQaO', '数据库管理员', 'IT部门', 'dba'),
('test_user', 'test@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfLkIwWQXjZzQaO', '测试用户', '测试部门', 'viewer')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

-- 创建存储过程用于生成测试数据
DELIMITER //

CREATE PROCEDURE GenerateTestData()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE max_records INT DEFAULT 1000;
    
    -- 生成产品数据
    WHILE i <= 100 DO
        INSERT INTO products (name, description, price, category_id, stock_quantity, status)
        VALUES (
            CONCAT('产品_', i),
            CONCAT('这是产品', i, '的详细描述'),
            ROUND(RAND() * 999 + 1, 2),
            FLOOR(RAND() * 8) + 1,
            FLOOR(RAND() * 100),
            CASE 
                WHEN RAND() < 0.8 THEN 'active'
                WHEN RAND() < 0.95 THEN 'inactive'
                ELSE 'discontinued'
            END
        );
        SET i = i + 1;
    END WHILE;
    
    -- 重置计数器
    SET i = 1;
    
    -- 生成订单数据
    WHILE i <= 200 DO
        INSERT INTO orders (user_id, order_number, total_amount, status, payment_status, shipping_address)
        VALUES (
            FLOOR(RAND() * 3) + 1,
            CONCAT('ORD', LPAD(i, 8, '0')),
            ROUND(RAND() * 999 + 10, 2),
            CASE 
                WHEN RAND() < 0.2 THEN 'pending'
                WHEN RAND() < 0.4 THEN 'processing'
                WHEN RAND() < 0.6 THEN 'shipped'
                WHEN RAND() < 0.9 THEN 'delivered'
                ELSE 'cancelled'
            END,
            CASE 
                WHEN RAND() < 0.8 THEN 'paid'
                WHEN RAND() < 0.95 THEN 'unpaid'
                ELSE 'refunded'
            END,
            CONCAT('测试地址', i)
        );
        SET i = i + 1;
    END WHILE;
    
    -- 重置计数器
    SET i = 1;
    
    -- 生成性能测试数据
    WHILE i <= max_records DO
        INSERT INTO performance_test (test_name, test_data, execution_time, memory_usage, cpu_usage, metadata)
        VALUES (
            CONCAT('性能测试_', i),
            REPEAT(CONCAT('测试数据', i, '_'), FLOOR(RAND() * 100) + 1),
            ROUND(RAND() * 10, 6),
            FLOOR(RAND() * 1024) + 256,
            ROUND(RAND() * 100, 2),
            JSON_OBJECT(
                'test_type', CASE FLOOR(RAND() * 3) 
                    WHEN 0 THEN 'cpu_intensive'
                    WHEN 1 THEN 'memory_intensive'
                    ELSE 'io_intensive'
                END,
                'priority', FLOOR(RAND() * 5) + 1,
                'tags', JSON_ARRAY('test', 'performance', 'mysql')
            )
        );
        SET i = i + 1;
    END WHILE;
    
END //

DELIMITER ;

-- 创建一些用于测试慢查询的视图
CREATE VIEW slow_query_test AS
SELECT 
    p.id,
    p.name,
    p.price,
    c.name as category_name,
    COUNT(oi.id) as order_count,
    SUM(oi.total_price) as total_sales,
    AVG(oi.unit_price) as avg_price
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'delivered'
GROUP BY p.id, p.name, p.price, c.name
HAVING total_sales > 100
ORDER BY total_sales DESC;

-- 创建复杂查询视图（用于性能测试）
CREATE VIEW complex_analytics AS
SELECT 
    DATE(o.created_at) as order_date,
    c.name as category_name,
    COUNT(DISTINCT o.id) as order_count,
    COUNT(DISTINCT o.user_id) as unique_customers,
    SUM(o.total_amount) as daily_revenue,
    AVG(o.total_amount) as avg_order_value,
    MAX(o.total_amount) as max_order_value,
    MIN(o.total_amount) as min_order_value
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
JOIN categories c ON p.category_id = c.id
WHERE o.status IN ('delivered', 'shipped')
    AND o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(o.created_at), c.name
ORDER BY order_date DESC, daily_revenue DESC;

-- 启用查询日志（用于监控慢查询）
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- 创建用于监控的用户
CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'monitor_password';
GRANT SELECT ON performance_schema.* TO 'monitor'@'%';
GRANT PROCESS ON *.* TO 'monitor'@'%';
FLUSH PRIVILEGES;

-- 输出初始化完成信息
SELECT 'MySQL数据库初始化完成！' as message;
SELECT 'UDBM MySQL测试环境已准备就绪' as status;
