# MySQL 性能指标详解

## 概述

MySQL是全球最流行的开源关系型数据库，本文档详细介绍MySQL的各项性能指标、数据来源、获取方式以及优化建议，帮助您全面掌握MySQL性能调优。

---

## 核心性能指标

### 1. CPU使用率

#### 指标说明
CPU使用率反映数据库服务器的计算资源消耗情况，是最直观的性能指标之一。

#### 数据来源
- **操作系统层面**：`top`、`htop`、`vmstat`
- **MySQL层面**：`SHOW STATUS LIKE 'Threads_running'`
- **性能监控工具**：Prometheus + node_exporter

#### 获取方式

**方法1：通过操作系统命令**
```bash
# 查看MySQL进程CPU使用率
top -p $(pidof mysqld)

# 查看所有CPU核心使用率
mpstat -P ALL 1

# 查看进程级别详细信息
pidstat -u -p $(pidof mysqld) 1
```

**方法2：通过MySQL状态变量**
```sql
-- 查看运行中的线程数（间接反映CPU压力）
SHOW STATUS LIKE 'Threads_running';

-- 查看累计CPU时间（需要performance_schema）
SELECT 
  SUM(SUM_TIMER_WAIT) / 1000000000000 AS total_cpu_seconds
FROM performance_schema.events_statements_summary_global_by_event_name;
```

**方法3：通过performance_schema精确分析**
```sql
-- 查看TOP 10消耗CPU的SQL
SELECT 
  DIGEST_TEXT,
  COUNT_STAR AS exec_count,
  SUM_TIMER_WAIT / 1000000000000 AS total_cpu_time_sec,
  AVG_TIMER_WAIT / 1000000000000 AS avg_cpu_time_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

#### 健康阈值
| 状态 | CPU使用率 | 说明 | 健康度影响 |
|------|-----------|------|------------|
| 🟢 优秀 | < 60% | 系统运行流畅，有充足余量 | 满分 |
| 🟡 良好 | 60-70% | 正常使用，需要关注 | -5分 |
| 🟠 警告 | 70-80% | 压力较大，考虑优化 | -10分 |
| 🔴 危险 | > 80% | 需要立即优化或扩容 | -20分 |

#### 优化建议

**短期优化**：
1. **识别并优化高CPU查询**
```sql
-- 查找当前执行时间长的查询
SELECT 
  id, user, host, db, command, time, state, info
FROM information_schema.PROCESSLIST
WHERE command != 'Sleep' AND time > 5
ORDER BY time DESC;

-- 杀掉异常查询
KILL QUERY thread_id;
```

2. **优化查询计划**
```sql
-- 使用EXPLAIN分析
EXPLAIN SELECT ...;

-- 添加合适的索引
ALTER TABLE table_name ADD INDEX idx_column (column);
```

**长期优化**：
1. **读写分离**：将读操作分散到从库
2. **连接池优化**：避免频繁建立连接的CPU开销
3. **升级硬件**：增加CPU核心数
4. **分库分表**：降低单库压力

---

### 2. 内存使用指标

#### 2.1 InnoDB Buffer Pool（缓冲池）

InnoDB Buffer Pool是MySQL最重要的内存结构，缓存表数据和索引，直接影响查询性能。

##### 数据来源
```sql
-- 查看Buffer Pool配置
SHOW VARIABLES LIKE 'innodb_buffer_pool%';

-- 查看Buffer Pool状态
SHOW STATUS LIKE 'Innodb_buffer_pool%';

-- 详细统计信息
SELECT * FROM information_schema.INNODB_BUFFER_POOL_STATS;
```

##### 核心指标

**1. Buffer Pool大小**
```sql
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
-- 建议：服务器内存的70-80%（专用数据库服务器）
```

**2. Buffer Pool命中率**
```sql
-- 计算命中率
SELECT 
  CONCAT(
    ROUND(
      (1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)) * 100, 
      2
    ), 
    '%'
  ) AS buffer_pool_hit_ratio,
  Innodb_buffer_pool_reads AS physical_reads,
  Innodb_buffer_pool_read_requests AS logical_reads
FROM (
  SELECT 
    VARIABLE_VALUE AS Innodb_buffer_pool_reads
  FROM performance_schema.global_status 
  WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'
) AS reads,
(
  SELECT 
    VARIABLE_VALUE AS Innodb_buffer_pool_read_requests
  FROM performance_schema.global_status 
  WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'
) AS requests;
```

**关键指标说明**：
- `Innodb_buffer_pool_reads`：从磁盘读取的次数（物理读）
- `Innodb_buffer_pool_read_requests`：从缓冲池读取的请求次数（逻辑读）
- **命中率公式**：`(1 - 物理读 / 逻辑读) × 100%`

**3. 脏页比率**
```sql
SELECT 
  VARIABLE_VALUE AS dirty_pages,
  (SELECT VARIABLE_VALUE 
   FROM performance_schema.global_status 
   WHERE VARIABLE_NAME = 'Innodb_buffer_pool_pages_total') AS total_pages,
  ROUND(
    (VARIABLE_VALUE / 
     (SELECT VARIABLE_VALUE 
      FROM performance_schema.global_status 
      WHERE VARIABLE_NAME = 'Innodb_buffer_pool_pages_total')) * 100,
    2
  ) AS dirty_pages_ratio
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Innodb_buffer_pool_pages_dirty';
```

##### 健康阈值
| 指标 | 优秀 | 良好 | 警告 | 危险 |
|------|------|------|------|------|
| 命中率 | ≥ 99% | 98-99% | 95-98% | < 95% |
| 脏页比率 | < 50% | 50-75% | 75-90% | > 90% |

##### 优化配置

**1. 调整Buffer Pool大小**
```ini
# my.cnf
[mysqld]
# 设置为服务器内存的70-80%
innodb_buffer_pool_size = 8G

# MySQL 5.7+支持在线调整
innodb_buffer_pool_chunk_size = 128M
innodb_buffer_pool_instances = 8  # 建议：每个实例1GB
```

**2. 优化刷新策略**
```ini
# 控制脏页刷新频率
innodb_max_dirty_pages_pct = 75        # 脏页比率上限
innodb_max_dirty_pages_pct_lwm = 10    # 开始预刷新的水位线

# IO容量配置（根据磁盘类型调整）
innodb_io_capacity = 2000               # SSD建议值
innodb_io_capacity_max = 4000           # 最大IO容量
```

**3. Buffer Pool预热**
```ini
# 自动保存和恢复Buffer Pool内容
innodb_buffer_pool_dump_at_shutdown = ON
innodb_buffer_pool_load_at_startup = ON
innodb_buffer_pool_dump_pct = 25        # 保存25%的热数据
```

**手动预热**：
```sql
-- 保存当前Buffer Pool内容
SET GLOBAL innodb_buffer_pool_dump_now = ON;

-- 恢复Buffer Pool内容
SET GLOBAL innodb_buffer_pool_load_now = ON;

-- 查看恢复进度
SHOW STATUS LIKE 'Innodb_buffer_pool_load_status';
```

---

### 3. 连接池指标

#### 核心连接指标

##### 数据来源
```sql
-- 连接相关状态变量
SHOW STATUS LIKE 'Threads%';
SHOW STATUS LIKE 'Connections';
SHOW STATUS LIKE 'Max_used_connections';
SHOW STATUS LIKE 'Aborted%';

-- 当前连接详情
SHOW PROCESSLIST;
SELECT * FROM information_schema.PROCESSLIST;
```

##### 关键指标说明

**1. 当前连接数**
```sql
SHOW STATUS LIKE 'Threads_connected';
-- 返回当前活跃连接数
```

**2. 最大连接数配置**
```sql
SHOW VARIABLES LIKE 'max_connections';
-- 默认值通常为151，生产环境建议500-2000
```

**3. 历史最大连接数**
```sql
SHOW STATUS LIKE 'Max_used_connections';
-- 反映历史峰值，用于评估配置是否充足
```

**4. 连接使用率**
```sql
SELECT 
  a.VARIABLE_VALUE AS current_connections,
  b.VARIABLE_VALUE AS max_used_connections,
  c.VARIABLE_VALUE AS max_connections,
  ROUND((b.VARIABLE_VALUE / c.VARIABLE_VALUE) * 100, 2) AS max_usage_ratio,
  ROUND((a.VARIABLE_VALUE / c.VARIABLE_VALUE) * 100, 2) AS current_usage_ratio
FROM 
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected') a,
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Max_used_connections') b,
  (SELECT VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'max_connections') c;
```

**5. 连接拒绝率**
```sql
SELECT 
  VARIABLE_VALUE AS aborted_connects,
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Connections') AS total_connections,
  ROUND(
    (VARIABLE_VALUE / 
     (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Connections')) * 100,
    4
  ) AS abort_ratio
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Aborted_connects';
```

##### 健康阈值
| 指标 | 优秀 | 良好 | 警告 | 危险 |
|------|------|------|------|------|
| 连接使用率 | < 70% | 70-80% | 80-90% | > 90% |
| 连接拒绝率 | 0% | < 0.1% | 0.1-1% | > 1% |
| 拒绝连接数 | 0 | < 10/小时 | 10-100/小时 | > 100/小时 |

##### 优化建议

**1. 调整最大连接数**
```sql
-- 临时调整（重启失效）
SET GLOBAL max_connections = 1000;

-- 永久配置（my.cnf）
[mysqld]
max_connections = 1000
```

**计算公式**：
```
max_connections = 
  (可用内存 - 系统保留 - Buffer Pool - 其他缓存) / 单连接内存

单连接内存 ≈ 
  read_buffer_size + 
  read_rnd_buffer_size + 
  sort_buffer_size + 
  join_buffer_size + 
  binlog_cache_size + 
  thread_stack
```

**2. 连接超时配置**
```ini
# my.cnf
wait_timeout = 600              # 非交互连接超时（秒）
interactive_timeout = 600       # 交互连接超时（秒）
connect_timeout = 10            # 连接建立超时（秒）
```

**3. 使用连接池**

**应用层连接池配置示例（HikariCP）**：
```yaml
hikari:
  maximum-pool-size: 20         # 最大连接数
  minimum-idle: 5               # 最小空闲连接
  connection-timeout: 30000     # 连接超时（毫秒）
  idle-timeout: 600000          # 空闲超时（毫秒）
  max-lifetime: 1800000         # 连接最大存活时间
```

**4. 监控长时间运行的连接**
```sql
-- 查找运行超过1小时的连接
SELECT 
  id, user, host, db, command, time, state, LEFT(info, 100) AS query
FROM information_schema.PROCESSLIST
WHERE command != 'Sleep' AND time > 3600
ORDER BY time DESC;

-- 杀掉僵尸连接
KILL CONNECTION thread_id;
```

---

### 4. 查询性能指标

#### 4.1 QPS (Queries Per Second)

##### 数据来源
```sql
-- 查询统计
SHOW STATUS LIKE 'Questions';
SHOW STATUS LIKE 'Queries';
SHOW STATUS LIKE 'Uptime';
```

##### 计算方法
```sql
-- 计算平均QPS
SELECT 
  ROUND(
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Questions') /
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Uptime'),
    2
  ) AS avg_qps;

-- 实时监控QPS（需要两次采样）
-- 第一次采样
SET @questions_before = (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Questions');
SET @time_before = UNIX_TIMESTAMP();

-- 等待1秒或更长时间
DO SLEEP(1);

-- 第二次采样并计算
SET @questions_after = (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Questions');
SET @time_after = UNIX_TIMESTAMP();

SELECT 
  (@questions_after - @questions_before) / (@time_after - @time_before) AS current_qps;
```

#### 4.2 TPS (Transactions Per Second)

##### 数据来源
```sql
-- 事务统计
SHOW STATUS LIKE 'Com_commit';
SHOW STATUS LIKE 'Com_rollback';
SHOW STATUS LIKE 'Handler_commit';
```

##### 计算方法
```sql
-- 计算平均TPS
SELECT 
  ROUND(
    ((SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Com_commit') +
     (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Com_rollback')) /
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Uptime'),
    2
  ) AS avg_tps;
```

#### 4.3 慢查询指标

##### 数据来源
```sql
-- 慢查询统计
SHOW STATUS LIKE 'Slow_queries';
SHOW VARIABLES LIKE 'long_query_time';
SHOW VARIABLES LIKE 'slow_query_log%';
```

##### 慢查询日志配置
```ini
# my.cnf
[mysqld]
slow_query_log = 1
slow_query_log_file = /var/log/mysql/mysql-slow.log
long_query_time = 2                      # 超过2秒记录
log_queries_not_using_indexes = 1        # 记录未使用索引的查询
min_examined_row_limit = 1000            # 扫描行数阈值
```

##### 分析慢查询

**1. 使用mysqldumpslow工具**
```bash
# 显示Top 10慢查询
mysqldumpslow -s t -t 10 /var/log/mysql/mysql-slow.log

# 按平均执行时间排序
mysqldumpslow -s at -t 10 /var/log/mysql/mysql-slow.log

# 按锁等待时间排序
mysqldumpslow -s l -t 10 /var/log/mysql/mysql-slow.log
```

**2. 使用pt-query-digest（Percona Toolkit）**
```bash
# 分析慢查询日志
pt-query-digest /var/log/mysql/mysql-slow.log > slow_query_report.txt

# 实时分析正在执行的查询
pt-query-digest --processlist h=localhost,u=root,p=password

# 按时间段分析
pt-query-digest --since '2025-10-01 00:00:00' \
                --until '2025-10-01 23:59:59' \
                /var/log/mysql/mysql-slow.log
```

**3. 通过performance_schema查询**
```sql
-- 查询执行统计（MySQL 5.7+）
SELECT 
  DIGEST_TEXT,
  COUNT_STAR AS exec_count,
  SUM_TIMER_WAIT / 1000000000000 AS total_time_sec,
  AVG_TIMER_WAIT / 1000000000000 AS avg_time_sec,
  SUM_ROWS_EXAMINED AS total_rows_examined,
  SUM_ROWS_SENT AS total_rows_sent
FROM performance_schema.events_statements_summary_by_digest
WHERE DIGEST_TEXT IS NOT NULL
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;
```

##### 健康阈值
| 指标 | 优秀 | 良好 | 警告 | 危险 |
|------|------|------|------|------|
| 慢查询比率 | < 0.5% | 0.5-1% | 1-3% | > 5% |
| 慢查询数量 | < 10/分钟 | 10-50/分钟 | 50-100/分钟 | > 100/分钟 |

##### 优化策略

**1. 索引优化**
```sql
-- 分析查询
EXPLAIN SELECT ...;

-- 查看索引使用情况
SHOW INDEX FROM table_name;

-- 添加索引
ALTER TABLE table_name ADD INDEX idx_column (column);

-- 创建复合索引（注意顺序）
ALTER TABLE table_name ADD INDEX idx_multi (col1, col2, col3);

-- 创建覆盖索引
ALTER TABLE table_name ADD INDEX idx_covering (col1, col2, col3, col4);
```

**2. 查询重写**
```sql
-- 避免SELECT *
SELECT col1, col2, col3 FROM table_name WHERE ...;

-- 使用LIMIT限制结果集
SELECT * FROM table_name WHERE ... LIMIT 1000;

-- 避免子查询，改用JOIN
-- 优化前
SELECT * FROM t1 WHERE id IN (SELECT t1_id FROM t2 WHERE ...);
-- 优化后
SELECT t1.* FROM t1 INNER JOIN t2 ON t1.id = t2.t1_id WHERE ...;

-- 避免函数操作索引列
-- 优化前
SELECT * FROM table_name WHERE DATE(created_at) = '2025-10-04';
-- 优化后
SELECT * FROM table_name 
WHERE created_at >= '2025-10-04 00:00:00' 
  AND created_at < '2025-10-05 00:00:00';
```

---

## InnoDB 存储引擎指标

### 1. InnoDB 事务与锁

#### 1.1 死锁监控

##### 数据来源
```sql
-- 查看最近一次死锁信息（MySQL 5.7及以下）
SHOW ENGINE INNODB STATUS\G

-- 查看死锁统计（MySQL 8.0+）
SHOW STATUS LIKE 'Innodb_deadlocks';
```

##### 死锁信息解读

**SHOW ENGINE INNODB STATUS 输出解析**：
```
------------------------
LATEST DETECTED DEADLOCK
------------------------
2025-10-04 14:30:00 0x7f8a2c001700
*** (1) TRANSACTION:
TRANSACTION 421234, ACTIVE 2 sec starting index read
mysql tables in use 1, locked 1
LOCK WAIT 3 lock struct(s), heap size 1136, 2 row lock(s)
MySQL thread id 42, OS thread handle 140234567890, query id 1234567 localhost root updating
UPDATE accounts SET balance = balance - 100 WHERE id = 1

*** (1) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 58 page no 3 n bits 72 index PRIMARY of table `test`.`accounts`
trx id 421234 lock_mode X locks rec but not gap waiting

*** (2) TRANSACTION:
TRANSACTION 421235, ACTIVE 1 sec starting index read
mysql tables in use 1, locked 1
3 lock struct(s), heap size 1136, 2 row lock(s)
MySQL thread id 43, OS thread handle 140234567891, query id 1234568 localhost root updating
UPDATE accounts SET balance = balance + 100 WHERE id = 2

*** (2) HOLDS THE LOCK(S):
RECORD LOCKS space id 58 page no 3 n bits 72 index PRIMARY of table `test`.`accounts`
trx id 421235 lock_mode X locks rec but not gap

*** (2) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 58 page no 3 n bits 72 index PRIMARY of table `test`.`accounts`
trx id 421235 lock_mode X locks rec but not gap waiting

*** WE ROLL BACK TRANSACTION (1)
```

##### 死锁预防策略

**1. 按固定顺序访问资源**
```sql
-- 不好的做法：不同事务以不同顺序访问
-- 事务1
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- 事务2
UPDATE accounts SET balance = balance - 50 WHERE id = 2;
UPDATE accounts SET balance = balance + 50 WHERE id = 1;

-- 好的做法：统一按ID升序访问
-- 事务1和事务2都按 id=1, id=2 的顺序访问
```

**2. 缩短事务长度**
```sql
-- 不好的做法：长事务持有锁时间长
START TRANSACTION;
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
-- 执行复杂业务逻辑...
-- 调用外部API...
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- 好的做法：减少事务内的业务逻辑
-- 先执行业务逻辑
-- 快速完成数据库事务
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;
```

**3. 使用适当的索引**
```sql
-- 减少锁的范围
ALTER TABLE table_name ADD INDEX idx_query_column (column);
```

**4. 降低隔离级别**
```sql
-- 如果业务允许，可以降低隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

#### 1.2 锁等待监控

##### 实时监控锁等待
```sql
-- MySQL 5.7及以下
SELECT 
  r.trx_id AS waiting_trx_id,
  r.trx_mysql_thread_id AS waiting_thread,
  r.trx_query AS waiting_query,
  b.trx_id AS blocking_trx_id,
  b.trx_mysql_thread_id AS blocking_thread,
  b.trx_query AS blocking_query
FROM information_schema.INNODB_LOCK_WAITS w
INNER JOIN information_schema.INNODB_TRX b ON b.trx_id = w.blocking_trx_id
INNER JOIN information_schema.INNODB_TRX r ON r.trx_id = w.requesting_trx_id;

-- MySQL 8.0+（推荐）
SELECT 
  waiting_pid AS waiting_thread_id,
  waiting_query,
  blocking_pid AS blocking_thread_id,
  blocking_query,
  wait_age AS wait_age_seconds
FROM sys.innodb_lock_waits;
```

##### 表锁等待统计
```sql
-- 表锁统计
SHOW STATUS LIKE 'Table_locks%';

-- 计算表锁等待比率
SELECT 
  a.VARIABLE_VALUE AS locks_waited,
  b.VARIABLE_VALUE AS locks_immediate,
  ROUND(
    (a.VARIABLE_VALUE / (a.VARIABLE_VALUE + b.VARIABLE_VALUE)) * 100,
    4
  ) AS lock_wait_ratio
FROM 
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Table_locks_waited') a,
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Table_locks_immediate') b;
```

##### 健康阈值
| 指标 | 优秀 | 良好 | 警告 | 危险 |
|------|------|------|------|------|
| 死锁频率 | 0次/小时 | 1-2次/小时 | 3-5次/小时 | > 10次/小时 |
| 表锁等待比率 | < 0.1% | 0.1-0.5% | 0.5-1% | > 1% |
| 锁等待事务数 | 0 | 1-3 | 4-10 | > 10 |

---

### 2. InnoDB IO 性能

#### 数据来源
```sql
-- IO相关状态
SHOW STATUS LIKE 'Innodb_data%';
SHOW STATUS LIKE 'Innodb_os_log%';
SHOW STATUS LIKE 'Innodb_pages%';
```

#### 关键IO指标

**1. 磁盘读写量**
```sql
SELECT 
  VARIABLE_NAME,
  VARIABLE_VALUE,
  CASE 
    WHEN VARIABLE_NAME LIKE '%read%' THEN 'Read'
    WHEN VARIABLE_NAME LIKE '%written%' THEN 'Write'
  END AS io_type
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
  'Innodb_data_read',
  'Innodb_data_written',
  'Innodb_data_reads',
  'Innodb_data_writes'
)
ORDER BY VARIABLE_NAME;
```

**2. Redo Log写入**
```sql
-- Redo Log IO统计
SELECT 
  VARIABLE_NAME,
  VARIABLE_VALUE / 1024 / 1024 AS value_mb
FROM performance_schema.global_status
WHERE VARIABLE_NAME LIKE 'Innodb_os_log%';
```

#### IO优化配置

**1. 调整IO容量**
```ini
# my.cnf
[mysqld]
# 基于磁盘类型设置
innodb_io_capacity = 2000               # SSD建议值：2000-4000
innodb_io_capacity_max = 4000           # 最大IO容量

# HDD建议值
# innodb_io_capacity = 200
# innodb_io_capacity_max = 400
```

**2. 刷新策略优化**
```ini
# 日志刷新策略
innodb_flush_log_at_trx_commit = 1      # 最安全（1），性能优先可设为2
# 1: 每次事务提交都刷新到磁盘（最安全）
# 2: 每次事务提交写入OS缓存，每秒刷新一次磁盘
# 0: 每秒写入OS缓存并刷新磁盘（性能最好，不推荐）

# 数据刷新策略
innodb_flush_method = O_DIRECT          # 跳过OS缓存，减少双重缓冲

# 脏页刷新
innodb_max_dirty_pages_pct = 75
innodb_max_dirty_pages_pct_lwm = 10
```

---

## 主从复制指标

### 核心指标监控

#### 数据来源
```sql
-- 从库执行
SHOW SLAVE STATUS\G
-- 或（MySQL 8.0+）
SHOW REPLICA STATUS\G
```

#### 关键指标说明

**1. 复制延迟（Seconds_Behind_Master）**
```sql
SHOW SLAVE STATUS\G

-- 关注以下字段：
-- Seconds_Behind_Master: 复制延迟（秒）
-- Slave_IO_Running: IO线程状态（应为Yes）
-- Slave_SQL_Running: SQL线程状态（应为Yes）
-- Last_Error: 最后错误信息
```

**2. 复制位点信息**
```
Master_Log_File: 主库binlog文件
Read_Master_Log_Pos: 已读取的位置
Relay_Log_File: 中继日志文件
Relay_Log_Pos: 中继日志位置
Exec_Master_Log_Pos: 已执行的主库位置
```

#### 健康阈值
| 指标 | 优秀 | 良好 | 警告 | 危险 |
|------|------|------|------|------|
| 复制延迟 | 0秒 | < 5秒 | 5-30秒 | > 60秒 |
| IO线程 | Running | Running | Connecting | Stopped |
| SQL线程 | Running | Running | - | Stopped |

#### 优化建议

**1. 并行复制（MySQL 5.7+）**
```ini
# my.cnf（从库配置）
[mysqld]
# 基于LOGICAL_CLOCK的并行复制
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers = 4              # 根据CPU核心数设置

# MySQL 8.0多线程复制
slave_preserve_commit_order = ON        # 保持提交顺序
```

**2. 半同步复制**
```sql
-- 主库安装插件
INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';

-- 从库安装插件
INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';

-- 主库启用半同步
SET GLOBAL rpl_semi_sync_master_enabled = 1;
SET GLOBAL rpl_semi_sync_master_timeout = 1000;  -- 1秒超时

-- 从库启用半同步
SET GLOBAL rpl_semi_sync_slave_enabled = 1;
```

**3. 监控复制延迟脚本**
```bash
#!/bin/bash
# check_replication_delay.sh

DELAY=$(mysql -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master" | awk '{print $2}')

if [ "$DELAY" == "NULL" ]; then
    echo "复制已停止！"
    exit 2
elif [ "$DELAY" -gt 60 ]; then
    echo "复制延迟严重: ${DELAY}秒"
    exit 2
elif [ "$DELAY" -gt 10 ]; then
    echo "复制延迟警告: ${DELAY}秒"
    exit 1
else
    echo "复制正常: 延迟${DELAY}秒"
    exit 0
fi
```

---

## 高级性能指标

### 1. 临时表使用

#### 数据来源
```sql
SHOW STATUS LIKE 'Created_tmp%';
```

#### 关键指标
```sql
SELECT 
  a.VARIABLE_VALUE AS tmp_tables,
  b.VARIABLE_VALUE AS tmp_disk_tables,
  ROUND(
    (b.VARIABLE_VALUE / a.VARIABLE_VALUE) * 100,
    2
  ) AS disk_tmp_table_ratio
FROM 
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Created_tmp_tables') a,
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Created_tmp_disk_tables') b;
```

#### 健康阈值
| 指标 | 优秀 | 良好 | 警告 | 危险 |
|------|------|------|------|------|
| 磁盘临时表比率 | < 10% | 10-20% | 20-30% | > 30% |

#### 优化配置
```ini
# my.cnf
[mysqld]
tmp_table_size = 256M           # 内存临时表大小
max_heap_table_size = 256M      # HEAP表最大值（需与tmp_table_size一致）

# 排序缓冲区
sort_buffer_size = 2M           # 每个连接的排序缓冲
read_buffer_size = 1M           # 顺序扫描缓冲
read_rnd_buffer_size = 1M       # 随机读缓冲
join_buffer_size = 2M           # JOIN缓冲
```

---

## MySQL 配置优化建议

### 全局配置模板

```ini
# my.cnf - MySQL 5.7/8.0 优化配置模板
# 适用于：32GB内存，8核CPU，SSD存储

[mysqld]
# ========== 基础配置 ==========
port = 3306
datadir = /var/lib/mysql
socket = /var/lib/mysql/mysql.sock
pid_file = /var/run/mysqld/mysqld.pid

# ========== InnoDB配置 ==========
# 缓冲池（服务器内存的70-80%）
innodb_buffer_pool_size = 24G
innodb_buffer_pool_instances = 8

# 日志文件
innodb_log_file_size = 2G
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 1
innodb_flush_method = O_DIRECT

# IO性能
innodb_io_capacity = 2000
innodb_io_capacity_max = 4000
innodb_read_io_threads = 4
innodb_write_io_threads = 4

# 脏页刷新
innodb_max_dirty_pages_pct = 75
innodb_max_dirty_pages_pct_lwm = 10

# 锁和事务
innodb_lock_wait_timeout = 50
innodb_deadlock_detect = ON

# ========== 连接配置 ==========
max_connections = 1000
max_connect_errors = 1000
wait_timeout = 600
interactive_timeout = 600
connect_timeout = 10

# ========== 查询缓存（MySQL 5.7，8.0已移除） ==========
# query_cache_type = 0
# query_cache_size = 0

# ========== 临时表配置 ==========
tmp_table_size = 256M
max_heap_table_size = 256M

# ========== 缓冲区配置 ==========
sort_buffer_size = 2M
read_buffer_size = 1M
read_rnd_buffer_size = 1M
join_buffer_size = 2M

# ========== 慢查询日志 ==========
slow_query_log = 1
slow_query_log_file = /var/log/mysql/mysql-slow.log
long_query_time = 2
log_queries_not_using_indexes = 1
min_examined_row_limit = 1000

# ========== 二进制日志 ==========
log_bin = /var/log/mysql/mysql-bin
binlog_format = ROW
binlog_expire_logs_seconds = 604800  # 7天
max_binlog_size = 1G
sync_binlog = 1

# ========== 复制配置 ==========
server_id = 1
gtid_mode = ON
enforce_gtid_consistency = ON
log_slave_updates = ON

# 并行复制
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers = 4
slave_preserve_commit_order = ON

# ========== 性能监控 ==========
performance_schema = ON
```

---

## 性能问题排查流程

### 问题诊断决策树

```
系统性能问题
    │
    ├── CPU高 (> 80%)
    │   ├── 查找高CPU查询 → EXPLAIN分析 → 添加索引
    │   ├── 优化复杂JOIN → 查询重写
    │   └── 考虑读写分离/分库分表
    │
    ├── 内存不足
    │   ├── Buffer Pool命中率低 → 增加innodb_buffer_pool_size
    │   ├── 临时表过多 → 增加tmp_table_size
    │   └── 连接过多 → 优化连接池配置
    │
    ├── IO瓶颈
    │   ├── Buffer Pool命中率低 → 增加缓冲池
    │   ├── 脏页刷新频繁 → 调整刷新策略
    │   └── 磁盘性能不足 → 升级SSD
    │
    ├── 锁等待严重
    │   ├── 查找阻塞事务 → KILL长事务
    │   ├── 死锁频繁 → 统一访问顺序
    │   └── 降低隔离级别（如果业务允许）
    │
    └── 复制延迟
        ├── SQL线程慢 → 启用并行复制
        ├── IO线程慢 → 检查网络/主库负载
        └── 大事务导致 → 拆分大事务
```

---

## 监控告警阈值推荐

| 告警级别 | 指标 | 阈值 | 处理时效 |
|----------|------|------|----------|
| 🔴 P1严重 | CPU使用率 | > 90% | 立即处理 |
| 🔴 P1严重 | 磁盘使用率 | > 90% | 立即处理 |
| 🔴 P1严重 | 连接拒绝 | > 100次/小时 | 立即处理 |
| 🔴 P1严重 | 复制停止 | IO/SQL线程=No | 立即处理 |
| 🟠 P2重要 | CPU使用率 | > 80% | 1小时内 |
| 🟠 P2重要 | Buffer Pool命中率 | < 95% | 1小时内 |
| 🟠 P2重要 | 复制延迟 | > 60秒 | 1小时内 |
| 🟠 P2重要 | 慢查询比率 | > 3% | 1小时内 |
| 🟡 P3一般 | 磁盘使用率 | > 80% | 24小时内 |
| 🟡 P3一般 | 死锁频率 | > 10次/小时 | 24小时内 |
| 🟡 P3一般 | 表碎片率 | > 20% | 72小时内 |

---

## 总结

MySQL性能优化是一个持续的过程，关键要点：

1. **监控先行**：建立完善的监控体系
2. **数据驱动**：基于实际数据做优化决策
3. **循序渐进**：先优化影响最大的指标
4. **测试验证**：优化后务必验证效果
5. **文档记录**：记录每次优化的过程和结果

**记住**：过早优化是万恶之源，先确保系统稳定，再追求极致性能！
