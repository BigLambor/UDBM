# PostgreSQL 性能指标详解

## 概述

PostgreSQL是功能强大的开源对象-关系型数据库系统，以其ACID兼容性、丰富的数据类型和可扩展性著称。本文档详细介绍PostgreSQL的各项性能指标、监控方法以及优化策略。

---

## 核心性能指标

### 1. 缓冲区命中率（Buffer Hit Ratio）

这是PostgreSQL最重要的性能指标之一，反映了数据在内存中的命中情况。

#### 指标说明
缓冲区命中率表示查询数据时从共享缓冲区（shared_buffers）读取的比例，而不是从磁盘读取。高命中率意味着更少的磁盘IO，更好的查询性能。

#### 数据来源
```sql
-- 查看数据库级别的命中率
SELECT 
  datname AS database,
  blks_hit,
  blks_read,
  CASE 
    WHEN (blks_hit + blks_read) = 0 THEN 0
    ELSE ROUND(
      (blks_hit::numeric / (blks_hit + blks_read)) * 100, 
      2
    )
  END AS hit_ratio
FROM pg_stat_database
WHERE datname IS NOT NULL
ORDER BY datname;
```

**关键指标说明**：
- `blks_hit`: 从缓冲区读取的数据块数（内存命中）
- `blks_read`: 从磁盘读取的数据块数（物理读）
- **命中率公式**: `blks_hit / (blks_hit + blks_read) × 100%`

#### 获取方式

**1. 实时查询**
```sql
-- 查看整体命中率
SELECT 
  sum(blks_hit) AS total_hits,
  sum(blks_read) AS total_reads,
  CASE 
    WHEN sum(blks_hit + blks_read) = 0 THEN 0
    ELSE ROUND(
      (sum(blks_hit)::numeric / sum(blks_hit + blks_read)) * 100,
      2
    )
  END AS overall_hit_ratio
FROM pg_stat_database;

-- 查看表级别命中率
SELECT 
  schemaname,
  tablename,
  heap_blks_hit,
  heap_blks_read,
  CASE 
    WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
    ELSE ROUND(
      (heap_blks_hit::numeric / (heap_blks_hit + heap_blks_read)) * 100,
      2
    )
  END AS table_hit_ratio
FROM pg_statio_user_tables
WHERE heap_blks_read > 0
ORDER BY heap_blks_read DESC
LIMIT 20;
```

**2. 索引命中率**
```sql
-- 查看索引命中率
SELECT 
  schemaname,
  tablename,
  indexrelname,
  idx_blks_hit,
  idx_blks_read,
  CASE 
    WHEN (idx_blks_hit + idx_blks_read) = 0 THEN 0
    ELSE ROUND(
      (idx_blks_hit::numeric / (idx_blks_hit + idx_blks_read)) * 100,
      2
    )
  END AS index_hit_ratio
FROM pg_statio_user_indexes
WHERE idx_blks_read > 0
ORDER BY idx_blks_read DESC
LIMIT 20;
```

#### 健康阈值
| 状态 | 命中率 | 说明 | 健康度影响 |
|------|--------|------|------------|
| 🟢 优秀 | ≥ 99% | 内存配置理想 | 满分 |
| 🟡 良好 | 98-99% | 可接受，有优化空间 | -5分 |
| 🟠 警告 | 95-98% | 需要增加内存 | -10分 |
| 🔴 危险 | < 95% | 严重性能问题 | -20分 |

#### 优化建议

**1. 调整shared_buffers**
```postgresql
-- postgresql.conf
# 建议：系统内存的25%（专用服务器）
# 32GB内存的服务器建议配置
shared_buffers = 8GB

# 重启PostgreSQL生效
sudo systemctl restart postgresql
```

**2. 调整effective_cache_size**
```postgresql
-- postgresql.conf
# 这个参数不会分配实际内存，只是告诉查询优化器可用的缓存大小
# 建议：系统内存的75%
effective_cache_size = 24GB
```

**3. 监控并预热热数据**
```sql
-- 使用pg_prewarm扩展预热表
CREATE EXTENSION IF NOT EXISTS pg_prewarm;

-- 预热整个表
SELECT pg_prewarm('tablename');

-- 预热表的前10万个块
SELECT pg_prewarm('tablename', 'buffer', 'main', 0, 100000);
```

**4. 分析缓冲区使用情况**
```sql
-- 安装pg_buffercache扩展
CREATE EXTENSION IF NOT EXISTS pg_buffercache;

-- 查看缓冲区中数据库对象的分布
SELECT 
  c.relname,
  count(*) AS buffers,
  pg_size_pretty(count(*) * 8192) AS buffer_size
FROM pg_buffercache b
INNER JOIN pg_class c ON b.relfilenode = pg_relation_filenode(c.oid)
WHERE b.reldatabase IN (
  0, 
  (SELECT oid FROM pg_database WHERE datname = current_database())
)
GROUP BY c.relname
ORDER BY count(*) DESC
LIMIT 20;
```

---

### 2. 连接数管理

#### 指标说明
PostgreSQL使用进程模型，每个连接对应一个独立的后端进程。连接数过多会消耗大量内存和系统资源。

#### 数据来源
```sql
-- 查看当前连接数
SELECT count(*) AS total_connections
FROM pg_stat_activity;

-- 查看各状态连接数
SELECT 
  state,
  count(*) AS count
FROM pg_stat_activity
WHERE pid <> pg_backend_pid()  -- 排除当前连接
GROUP BY state
ORDER BY count DESC;

-- 查看按数据库分组的连接数
SELECT 
  datname AS database,
  count(*) AS connections
FROM pg_stat_activity
GROUP BY datname
ORDER BY connections DESC;

-- 查看按用户分组的连接数
SELECT 
  usename AS username,
  count(*) AS connections
FROM pg_stat_activity
GROUP BY usename
ORDER BY connections DESC;
```

#### 连接状态说明
| 状态 | 说明 |
|------|------|
| `active` | 正在执行查询 |
| `idle` | 空闲，等待客户端命令 |
| `idle in transaction` | 事务中空闲（需关注） |
| `idle in transaction (aborted)` | 事务中空闲（已出错） |
| `fastpath function call` | 执行fast-path函数 |
| `disabled` | 连接已禁用 |

#### 健康阈值
```sql
-- 查看最大连接数配置
SHOW max_connections;

-- 计算连接使用率
SELECT 
  count(*) AS current_connections,
  (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections,
  ROUND(
    (count(*)::numeric / 
     (SELECT setting::int FROM pg_settings WHERE name = 'max_connections')) * 100,
    2
  ) AS usage_ratio
FROM pg_stat_activity;
```

| 状态 | 使用率 | 建议措施 |
|------|--------|----------|
| 🟢 正常 | < 70% | 无需处理 |
| 🟡 关注 | 70-80% | 考虑使用连接池 |
| 🟠 警告 | 80-90% | 增加max_connections或使用连接池 |
| 🔴 危险 | > 90% | 立即处理，可能拒绝新连接 |

#### 优化建议

**1. 调整最大连接数**
```postgresql
-- postgresql.conf
# 根据内存和CPU计算合适的值
max_connections = 200

# 每个连接约占用5-10MB内存
# 计算公式：max_connections < (总内存 - shared_buffers - OS保留) / 单连接内存
```

**2. 使用连接池（强烈推荐）**

**PgBouncer配置示例**：
```ini
# pgbouncer.ini
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# 连接池模式
pool_mode = transaction  # session/transaction/statement

# 连接池大小
default_pool_size = 25          # 每个数据库用户组合的默认连接池大小
min_pool_size = 10              # 最小连接数
max_client_conn = 1000          # 最大客户端连接数
max_db_connections = 100        # 后端数据库最大连接数
```

**3. 清理空闲连接**
```sql
-- 查找长时间空闲的连接（超过30分钟）
SELECT 
  pid,
  usename,
  datname,
  application_name,
  client_addr,
  state,
  state_change,
  now() - state_change AS idle_duration
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '30 minutes'
ORDER BY state_change;

-- 终止空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '30 minutes';
```

**4. 自动清理空闲连接**
```postgresql
-- postgresql.conf
# PostgreSQL 14+支持
idle_in_transaction_session_timeout = 600000  # 10分钟（毫秒）
idle_session_timeout = 3600000                # 1小时（毫秒）
```

---

### 3. 表膨胀（Table Bloat）

这是PostgreSQL特有的重要问题，由MVCC（多版本并发控制）机制导致。

#### 指标说明
PostgreSQL使用MVCC实现并发控制，UPDATE和DELETE操作会产生"死元组"（dead tuples）。如果不及时清理，会导致表膨胀，影响查询性能和磁盘空间。

#### 数据来源
```sql
-- 查看表统计信息
SELECT 
  schemaname,
  tablename,
  n_live_tup AS live_tuples,
  n_dead_tup AS dead_tuples,
  CASE 
    WHEN n_live_tup = 0 THEN 0
    ELSE ROUND((n_dead_tup::numeric / n_live_tup) * 100, 2)
  END AS dead_tuple_ratio,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY n_dead_tup DESC
LIMIT 20;
```

#### 精确计算表膨胀

**使用pgstattuple扩展**：
```sql
-- 安装扩展
CREATE EXTENSION IF NOT EXISTS pgstattuple;

-- 查看表膨胀详情
SELECT 
  tablename,
  pg_size_pretty(table_len) AS table_size,
  round(dead_tuple_percent, 2) AS dead_tuple_percent,
  pg_size_pretty((table_len * dead_tuple_percent / 100)::bigint) AS wasted_size
FROM pgstattuple('tablename');

-- 批量检查所有表（谨慎使用，会全表扫描）
SELECT 
  schemaname || '.' || tablename AS table_name,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  (pgstattuple(schemaname||'.'||tablename)).dead_tuple_percent AS bloat_pct
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND pg_total_relation_size(schemaname||'.'||tablename) > 100000000  -- >100MB
ORDER BY (pgstattuple(schemaname||'.'||tablename)).dead_tuple_percent DESC
LIMIT 10;
```

#### 健康阈值
| 死元组比率 | 状态 | 健康度影响 | 建议措施 |
|------------|------|------------|----------|
| < 5% | 🟢 优秀 | 无影响 | 保持AutoVacuum |
| 5-10% | 🟡 良好 | -5分 | 关注AutoVacuum执行 |
| 10-20% | 🟠 警告 | -10分 | 手动执行VACUUM |
| 20-30% | 🔴 危险 | -15分 | 立即执行VACUUM |
| > 30% | 🔴 严重 | -20分 | 考虑VACUUM FULL |

#### 优化建议

**1. 优化AutoVacuum配置**
```postgresql
-- postgresql.conf - 全局配置
autovacuum = on
autovacuum_max_workers = 4              # 并发worker数量
autovacuum_naptime = 30s                # 检查间隔（默认1分钟）

# 降低触发阈值，更频繁地清理
autovacuum_vacuum_scale_factor = 0.05   # 5%脏数据触发（默认20%）
autovacuum_analyze_scale_factor = 0.05  # 5%变更触发ANALYZE

# 提高VACUUM优先级
autovacuum_vacuum_cost_limit = 2000     # 增加成本限制（默认200）
autovacuum_vacuum_cost_delay = 10ms     # 降低延迟（默认20ms）

# 防止事务ID回卷
autovacuum_freeze_max_age = 200000000
```

**2. 针对高频更新表的优化**
```sql
-- 为特定表设置更激进的AutoVacuum策略
ALTER TABLE high_update_table 
SET (
  autovacuum_vacuum_scale_factor = 0.01,  -- 1%触发
  autovacuum_analyze_scale_factor = 0.01,
  autovacuum_vacuum_cost_delay = 5,       -- 更快清理
  autovacuum_vacuum_cost_limit = 5000
);

-- 查看表的AutoVacuum配置
SELECT 
  schemaname,
  tablename,
  reloptions
FROM pg_tables
WHERE reloptions IS NOT NULL;
```

**3. 手动VACUUM**
```sql
-- 普通VACUUM（不锁表，可在线执行）
VACUUM VERBOSE ANALYZE tablename;

-- 查看VACUUM进度（PostgreSQL 12+）
SELECT 
  pid,
  datname,
  relid::regclass AS table,
  phase,
  heap_blks_total,
  heap_blks_scanned,
  heap_blks_vacuumed,
  index_vacuum_count,
  max_dead_tuples,
  num_dead_tuples
FROM pg_stat_progress_vacuum;
```

**4. VACUUM FULL（谨慎使用）**
```sql
-- VACUUM FULL会锁表并重建表，回收所有空间
-- 仅在业务低峰期执行
VACUUM FULL VERBOSE tablename;

-- 更好的替代方案：使用pg_repack
-- pg_repack可以在线重组表，不锁表
-- 需要安装pg_repack扩展
pg_repack -d mydb -t tablename
```

**5. 监控长事务**
```sql
-- 长事务会阻止VACUUM清理死元组
SELECT 
  pid,
  usename,
  datname,
  state,
  now() - xact_start AS transaction_duration,
  query
FROM pg_stat_activity
WHERE state != 'idle'
  AND xact_start IS NOT NULL
  AND now() - xact_start > interval '10 minutes'
ORDER BY xact_start;

-- 终止长事务（谨慎！）
SELECT pg_terminate_backend(pid);
```

---

### 4. WAL (Write-Ahead Logging) 性能

#### 指标说明
WAL是PostgreSQL的预写式日志系统，所有数据修改都先写入WAL，确保事务的持久性和数据恢复能力。

#### 数据来源（PostgreSQL 14+）
```sql
-- 查看WAL统计信息
SELECT * FROM pg_stat_wal;

-- 关键字段说明：
-- wal_records: WAL记录数
-- wal_fpi: Full Page Images数量
-- wal_bytes: WAL写入字节数
-- wal_buffers_full: WAL缓冲区满的次数（需要关注）
-- wal_write: WAL写入次数
-- wal_sync: WAL同步次数
-- wal_write_time: WAL写入时间（毫秒）
-- wal_sync_time: WAL同步时间（毫秒）
```

#### 监控WAL生成速率
```sql
-- 监控WAL生成速率（需要两次采样）
-- 第一次采样
CREATE TEMP TABLE wal_stats_start AS
SELECT 
  now() AS sample_time,
  pg_current_wal_lsn() AS wal_lsn,
  wal_records,
  wal_bytes
FROM pg_stat_wal;

-- 等待一段时间（如60秒）
SELECT pg_sleep(60);

-- 第二次采样并计算速率
SELECT 
  ROUND(
    (current.wal_bytes - start.wal_bytes) / 
    EXTRACT(EPOCH FROM (current.sample_time - start.sample_time)) / 1024 / 1024,
    2
  ) AS wal_mb_per_second,
  pg_size_pretty(
    pg_wal_lsn_diff(current.wal_lsn, start.wal_lsn)
  ) AS wal_generated
FROM 
  wal_stats_start start,
  (SELECT 
     now() AS sample_time,
     pg_current_wal_lsn() AS wal_lsn,
     wal_records,
     wal_bytes
   FROM pg_stat_wal) current;
```

#### 健康阈值
| 指标 | 正常 | 警告 | 危险 |
|------|------|------|------|
| WAL缓冲区满次数 | 0 | < 100/小时 | > 1000/小时 |
| WAL写入延迟 | < 10ms | 10-50ms | > 100ms |
| WAL同步延迟 | < 20ms | 20-100ms | > 200ms |

#### 优化建议

**1. 调整WAL配置**
```postgresql
-- postgresql.conf
# WAL缓冲区
wal_buffers = 16MB              # 默认-1（自动，约为shared_buffers的1/32）

# WAL文件大小
max_wal_size = 4GB              # 最大WAL大小（触发checkpoint）
min_wal_size = 1GB              # 最小WAL大小

# WAL压缩
wal_compression = on            # 启用WAL压缩（减少磁盘IO）

# Checkpoint配置
checkpoint_timeout = 15min      # Checkpoint间隔
checkpoint_completion_target = 0.9  # 在checkpoint_timeout的90%内完成

# WAL写入模式
wal_sync_method = fdatasync     # Linux推荐值
```

**2. 异步提交（适合能容忍少量数据丢失的场景）**
```postgresql
-- 全局配置
synchronous_commit = off        # 异步提交，提高性能但可能丢失少量数据

-- 或者在会话级别设置
SET synchronous_commit = off;
-- 执行大批量写入
INSERT INTO ...;
-- 恢复同步提交
SET synchronous_commit = on;
```

**3. 监控Checkpoint频率**
```sql
-- 查看checkpoint统计
SELECT 
  checkpoints_timed,
  checkpoints_req,
  checkpoint_write_time / 1000 AS write_time_seconds,
  checkpoint_sync_time / 1000 AS sync_time_seconds,
  buffers_checkpoint,
  buffers_clean,
  buffers_backend
FROM pg_stat_bgwriter;

-- 如果checkpoints_req远大于checkpoints_timed，说明max_wal_size太小
```

---

### 5. 索引健康度

#### 监控索引使用情况
```sql
-- 查找未使用的索引
SELECT 
  schemaname,
  tablename,
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'  -- 排除主键
ORDER BY pg_relation_size(indexrelid) DESC;

-- 查找使用率高的索引
SELECT 
  schemaname,
  tablename,
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan > 1000
ORDER BY idx_scan DESC
LIMIT 20;
```

#### 检查索引膨胀
```sql
-- 使用pgstattuple检查索引膨胀
SELECT 
  schemaname || '.' || tablename AS table_name,
  indexrelname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
  (pgstatindex(indexrelid)).avg_leaf_density AS leaf_density,
  (pgstatindex(indexrelid)).leaf_fragmentation AS fragmentation
FROM pg_stat_user_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND pg_relation_size(indexrelid) > 10000000  -- >10MB
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;
```

#### 优化建议

**1. 删除未使用的索引**
```sql
-- 谨慎！确认索引确实未使用
DROP INDEX IF EXISTS unused_index_name;
```

**2. 重建膨胀的索引**
```sql
-- 方法1：REINDEX（锁表）
REINDEX INDEX CONCURRENTLY index_name;

-- 方法2：重建索引（推荐，PostgreSQL 12+）
CREATE INDEX CONCURRENTLY new_index_name ON table_name (column);
DROP INDEX CONCURRENTLY old_index_name;
```

---

## 查询性能分析

### 1. 慢查询监控

#### 配置慢查询日志
```postgresql
-- postgresql.conf
log_min_duration_statement = 1000  # 记录执行时间>1秒的查询（毫秒）
log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '
log_statement = 'none'             # 或'all'记录所有语句
log_duration = off                 # 或on记录所有查询执行时间
```

#### 使用pg_stat_statements
```sql
-- 安装扩展（需要重启PostgreSQL）
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 查看Top 20慢查询
SELECT 
  queryid,
  substring(query, 1, 100) AS query_preview,
  calls,
  ROUND(total_exec_time::numeric / 1000, 2) AS total_time_seconds,
  ROUND(mean_exec_time::numeric, 2) AS mean_time_ms,
  ROUND(stddev_exec_time::numeric, 2) AS stddev_time_ms,
  rows
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC
LIMIT 20;

-- 查看慢查询详情
SELECT 
  queryid,
  query,
  calls,
  total_exec_time / 1000 AS total_seconds,
  mean_exec_time AS avg_ms,
  max_exec_time AS max_ms,
  rows,
  ROUND((100.0 * total_exec_time / sum(total_exec_time) OVER ()), 2) AS percentage
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- 重置统计数据
SELECT pg_stat_statements_reset();
```

### 2. 执行计划分析

#### EXPLAIN命令
```sql
-- 查看执行计划
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- 查看详细执行计划
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
SELECT * FROM users WHERE email = 'test@example.com';

-- 输出JSON格式（便于程序解析）
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM users WHERE email = 'test@example.com';
```

#### 执行计划关键指标
- **Seq Scan**: 全表扫描（需要关注）
- **Index Scan**: 索引扫描（好）
- **Bitmap Index Scan**: 位图索引扫描
- **cost**: 估算成本（不是实际时间）
- **rows**: 估算行数
- **actual time**: 实际执行时间（需要ANALYZE）
- **Buffers**: 缓冲区使用情况

---

## PostgreSQL配置优化建议

### 全局配置模板

```postgresql
# postgresql.conf - PostgreSQL 14+ 优化配置
# 适用于：32GB内存，8核CPU，SSD存储

# ========== 内存配置 ==========
shared_buffers = 8GB                    # 系统内存的25%
effective_cache_size = 24GB              # 系统内存的75%
work_mem = 64MB                         # 单个查询操作的内存
maintenance_work_mem = 2GB              # 维护操作（VACUUM, CREATE INDEX）内存
max_stack_depth = 2MB

# ========== 连接配置 ==========
max_connections = 200                   # 建议使用连接池，保持较小值
superuser_reserved_connections = 3

# ========== WAL配置 ==========
wal_level = replica                     # 支持复制和归档
wal_buffers = 16MB
max_wal_size = 4GB
min_wal_size = 1GB
wal_compression = on
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9

# ========== 查询优化器 ==========
random_page_cost = 1.1                  # SSD建议值（HDD为4.0）
effective_io_concurrency = 200          # SSD建议值
default_statistics_target = 100         # 统计信息采样目标

# ========== AutoVacuum配置 ==========
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 30s
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_scale_factor = 0.05
autovacuum_vacuum_cost_limit = 2000
autovacuum_vacuum_cost_delay = 10ms

# ========== 日志配置 ==========
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000       # 记录>1秒的查询
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on                     # 记录锁等待
log_temp_files = 0                      # 记录临时文件使用
log_autovacuum_min_duration = 0         # 记录AutoVacuum活动

# ========== 并行查询 ==========
max_worker_processes = 8
max_parallel_workers = 8
max_parallel_workers_per_gather = 4
parallel_setup_cost = 1000
parallel_tuple_cost = 0.1

# ========== 其他优化 ==========
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

---

## 性能问题排查

### 常见问题诊断

**1. CPU高**
```sql
-- 查找CPU密集查询
SELECT 
  pid,
  usename,
  datname,
  state,
  now() - query_start AS duration,
  LEFT(query, 100) AS query
FROM pg_stat_activity
WHERE state = 'active'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- 终止长时间运行的查询
SELECT pg_terminate_backend(pid);
```

**2. 内存不足**
```sql
-- 检查临时文件使用（说明work_mem不足）
SELECT 
  datname,
  temp_files AS num_temp_files,
  pg_size_pretty(temp_bytes) AS temp_file_size
FROM pg_stat_database
WHERE temp_files > 0
ORDER BY temp_bytes DESC;
```

**3. 锁等待**
```sql
-- 查看锁等待
SELECT 
  blocked_locks.pid AS blocked_pid,
  blocked_activity.usename AS blocked_user,
  blocking_locks.pid AS blocking_pid,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

---

## 监控告警阈值

| 告警级别 | 指标 | 阈值 |
|----------|------|------|
| 🔴 P1严重 | 缓冲区命中率 | < 90% |
| 🔴 P1严重 | 连接数 | > 90% max_connections |
| 🔴 P1严重 | 复制延迟 | > 300秒 |
| 🟠 P2重要 | 死元组比率 | > 20% |
| 🟠 P2重要 | WAL缓冲区满 | > 100次/小时 |
| 🟠 P2重要 | AutoVacuum阻塞 | > 6小时未执行 |
| 🟡 P3一般 | 临时文件使用 | > 1GB/小时 |

---

## 总结

PostgreSQL性能优化关键点：

1. **缓冲区命中率**：保持≥99%，这是最重要的指标
2. **表膨胀**：定期VACUUM，保持死元组比率<5%
3. **连接池**：使用PgBouncer等连接池，避免连接数过多
4. **索引**：创建合适的索引，定期清理未使用的索引
5. **AutoVacuum**：根据业务特点调整AutoVacuum策略
6. **监控**：使用pg_stat_statements持续监控慢查询

**记住**：PostgreSQL的MVCC机制决定了需要特别关注VACUUM和表膨胀问题！
