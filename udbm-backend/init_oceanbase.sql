-- UDBM OceanBase 数据库初始化脚本
-- 统一数据库管理平台 - OceanBase测试数据库

-- 创建测试数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS udbm_oceanbase_demo;
USE udbm_oceanbase_demo;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    department VARCHAR(100),
    role VARCHAR(20) DEFAULT 'viewer',
    is_active TINYINT(1) DEFAULT 1,
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
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category_id BIGINT,
    stock_quantity INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_category (category_id),
    INDEX idx_status (status)
);

-- 创建分类表
CREATE TABLE IF NOT EXISTS categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    parent_id BIGINT,
    level INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_parent (parent_id),
    INDEX idx_level (level)
);

-- 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_number (order_number),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);

-- 创建订单详情表
CREATE TABLE IF NOT EXISTS order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
);

-- 创建库存变动记录表
CREATE TABLE IF NOT EXISTS inventory_movements (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id BIGINT NOT NULL,
    movement_type VARCHAR(20) NOT NULL, -- 'in', 'out', 'adjustment'
    quantity INT NOT NULL,
    reference_type VARCHAR(50), -- 'order', 'purchase', 'adjustment'
    reference_id BIGINT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    INDEX idx_product_id (product_id),
    INDEX idx_movement_type (movement_type),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_reference (reference_type, reference_id)
);

-- 创建审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    record_id BIGINT,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_table_record (table_name, record_id),
    INDEX idx_created_at (created_at DESC)
);

-- 插入初始数据

-- 插入用户数据
INSERT IGNORE INTO users (username, email, password_hash, full_name, department, role) VALUES
('admin', 'admin@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.mKOxYVYL6', '系统管理员', 'IT部门', 'admin'),
('dba_user', 'dba@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.mKOxYVYL6', '数据库管理员', 'IT部门', 'dba'),
('operator', 'operator@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.mKOxYVYL6', '运维人员', 'IT部门', 'operator'),
('viewer', 'viewer@udbm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.mKOxYVYL6', '查看用户', '业务部门', 'viewer');

-- 插入分类数据
INSERT IGNORE INTO categories (name, description, parent_id, level) VALUES
('电子产品', '各种电子设备和配件', NULL, 1),
('服装鞋帽', '服装、鞋子、帽子等', NULL, 1),
('图书音像', '书籍、音乐、视频等', NULL, 1),
('手机通讯', '手机及通讯设备', 1, 2),
('电脑办公', '电脑及办公设备', 1, 2),
('男装', '男士服装', 2, 2),
('女装', '女士服装', 2, 2);

-- 插入产品数据
INSERT IGNORE INTO products (name, description, price, category_id, stock_quantity, status) VALUES
('iPhone 15 Pro', '苹果最新旗舰手机', 7999.00, 4, 50, 'active'),
('MacBook Pro M3', '苹果笔记本电脑', 14999.00, 5, 30, 'active'),
('AirPods Pro', '苹果无线耳机', 1999.00, 4, 100, 'active'),
('ThinkPad X1', '联想商务笔记本', 8999.00, 5, 25, 'active'),
('Nike Air Max', '耐克运动鞋', 899.00, 6, 80, 'active'),
('Adidas T恤', '阿迪达斯运动T恤', 299.00, 6, 150, 'active'),
('Python编程指南', 'Python学习教程', 89.00, 3, 200, 'active'),
('数据库原理', '数据库基础教程', 119.00, 3, 120, 'active');

-- 插入订单数据
INSERT IGNORE INTO orders (order_number, user_id, total_amount, status, payment_status, shipping_address) VALUES
('ORD20241001001', 1, 7999.00, 'completed', 'paid', '北京市朝阳区某某街道123号'),
('ORD20241001002', 2, 16998.00, 'processing', 'paid', '上海市浦东新区某某路456号'),
('ORD20241001003', 3, 899.00, 'shipped', 'paid', '广州市天河区某某大道789号'),
('ORD20241001004', 4, 208.00, 'pending', 'unpaid', '深圳市南山区某某街101号');

-- 插入订单详情数据
INSERT IGNORE INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES
(1, 1, 1, 7999.00, 7999.00),
(2, 1, 1, 7999.00, 7999.00),
(2, 2, 1, 14999.00, 8999.00),
(3, 5, 1, 899.00, 899.00),
(4, 7, 1, 89.00, 89.00),
(4, 8, 1, 119.00, 119.00);

-- 插入库存变动记录
INSERT IGNORE INTO inventory_movements (product_id, movement_type, quantity, reference_type, reference_id, notes, created_by) VALUES
(1, 'out', -1, 'order', 1, '订单出库', 1),
(1, 'out', -1, 'order', 2, '订单出库', 1),
(5, 'out', -1, 'order', 3, '订单出库', 1),
(7, 'out', -1, 'order', 4, '订单出库', 1),
(8, 'out', -1, 'order', 4, '订单出库', 1);

-- 插入审计日志
INSERT IGNORE INTO audit_logs (user_id, action, table_name, record_id, new_values, ip_address) VALUES
(1, 'CREATE', 'orders', 1, '{"order_number": "ORD20241001001", "total_amount": 7999.00}', '192.168.1.100'),
(2, 'CREATE', 'orders', 2, '{"order_number": "ORD20241001002", "total_amount": 16998.00}', '192.168.1.101'),
(3, 'CREATE', 'orders', 3, '{"order_number": "ORD20241001003", "total_amount": 899.00}', '192.168.1.102'),
(4, 'CREATE', 'orders', 4, '{"order_number": "ORD20241001004", "total_amount": 208.00}', '192.168.1.103');

-- 创建一些测试视图
CREATE OR REPLACE VIEW order_summary AS
SELECT 
    o.id,
    o.order_number,
    u.username,
    u.full_name,
    o.total_amount,
    o.status,
    o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id;

CREATE OR REPLACE VIEW product_inventory AS
SELECT 
    p.id,
    p.name,
    p.price,
    p.stock_quantity,
    c.name as category_name,
    p.status
FROM products p
LEFT JOIN categories c ON p.category_id = c.id;

-- 创建存储过程示例（OceanBase支持）
DELIMITER //
CREATE PROCEDURE GetUserOrders(IN user_id BIGINT)
BEGIN
    SELECT 
        o.order_number,
        o.total_amount,
        o.status,
        o.created_at,
        GROUP_CONCAT(p.name) as products
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN products p ON oi.product_id = p.id
    WHERE o.user_id = user_id
    GROUP BY o.id
    ORDER BY o.created_at DESC;
END //
DELIMITER ;

-- 创建触发器示例
DELIMITER //
CREATE TRIGGER update_inventory_after_order
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE products 
    SET stock_quantity = stock_quantity - NEW.quantity 
    WHERE id = NEW.product_id;
    
    INSERT INTO inventory_movements (
        product_id, 
        movement_type, 
        quantity, 
        reference_type, 
        reference_id, 
        notes
    ) VALUES (
        NEW.product_id, 
        'out', 
        -NEW.quantity, 
        'order', 
        NEW.order_id, 
        'Auto inventory update from order'
    );
END //
DELIMITER ;

-- 提交事务
COMMIT;
