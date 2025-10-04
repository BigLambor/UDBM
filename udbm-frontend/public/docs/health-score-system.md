# 健康度指标体系详解

## 概述

健康度指标是评估数据库系统运行状态的**核心复合性指标**，通过整合多个维度的性能数据，提供0-100分的综合评分，帮助用户快速识别系统整体健康状况。

### 健康度指标的价值

- 🎯 **全局视图**：一个分数快速了解系统整体状态
- 📊 **横向对比**：支持多个数据库实例的健康度对比
- 🚨 **预警机制**：健康度下降趋势可预测潜在问题
- 💡 **优化指导**：指明最值得优化的维度和指标
- 📈 **趋势分析**：通过历史健康度分析系统演进

---

## 通用健康度计算模型

### 核心计算公式

```
健康度评分 = Σ(维度得分 × 维度权重) × 100

其中：
- 维度得分：单个维度的标准化得分（0-1之间）
- 维度权重：该维度在整体评分中的重要性（所有权重总和为1）
```

### 评分维度体系

健康度评分由5个核心维度组成：

| 维度 | 权重 | 说明 | 关键指标 |
|------|------|------|----------|
| 🚀 **性能维度** | 40% | 系统响应能力和处理效率 | CPU、内存、缓存命中率、查询响应时间 |
| ✅ **可用性维度** | 25% | 系统服务能力和稳定性 | 连接成功率、慢查询比率、错误率 |
| 📉 **稳定性维度** | 20% | 系统波动性和一致性 | 资源波动、锁等待、复制延迟 |
| 💾 **容量维度** | 10% | 资源余量和扩展空间 | 存储余量、连接池使用率、内存余量 |
| 🔧 **维护健康度** | 5% | 维护任务执行情况 | 备份完整性、表维护、统计信息 |

### 评分等级划分

| 等级 | 分数区间 | 状态 | 颜色 | 描述 | 建议措施 |
|------|----------|------|------|------|----------|
| 🌟 **优秀** | 90-100 | Excellent | 🟢 绿色 | 系统运行优秀 | 保持现状，持续监控 |
| 👍 **良好** | 75-89 | Good | 🟡 黄色 | 系统运行良好 | 关注潜在问题，有优化空间 |
| ⚠️ **警告** | 60-74 | Warning | 🟠 橙色 | 存在性能问题 | 需要采取优化措施 |
| 🚨 **危险** | 40-59 | Critical | 🔴 红色 | 存在严重问题 | 立即进行故障排查和优化 |
| 💥 **严重** | 0-39 | Severe | 🔴 深红 | 系统异常严重 | 紧急处理，可能影响业务 |

---

## MySQL 健康度计算模型

### 整体计算公式

```python
MySQL健康度 = (
    性能得分 × 0.40 +
    可用性得分 × 0.25 +
    稳定性得分 × 0.20 +
    容量得分 × 0.10 +
    存储引擎健康度 × 0.05
) × 100
```

### 1. 性能得分（40%权重）

性能得分是MySQL健康度的最重要组成部分，评估系统的处理能力和响应速度。

#### 计算公式

```python
性能得分 = (
    CPU得分 × 0.30 +
    内存得分 × 0.25 +
    InnoDB缓冲池命中率得分 × 0.20 +
    查询性能得分 × 0.15 +
    IO性能得分 × 0.10
)
```

#### 详细指标说明

##### CPU得分（12%总权重）

**数据来源**：
- `SHOW STATUS LIKE 'Threads_running'`
- 操作系统监控（top、vmstat）

**计算方法**：
```
CPU得分 = 1 - (CPU使用率 / 100)

分段评分：
- CPU < 60%: 得分 1.0（优秀）
- CPU 60-70%: 得分 0.9-1.0（良好）
- CPU 70-80%: 得分 0.7-0.9（警告）
- CPU > 80%: 得分 < 0.7（危险，指数衰减）
```

**业界最佳实践**：
- 保持CPU使用率在60%以下，为突发流量留出缓冲
- 持续80%以上表示需要优化或扩容
- 关注单核CPU使用率，避免单线程瓶颈

##### InnoDB缓冲池命中率得分（8%总权重）

**数据来源**：
```sql
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read%';

-- 计算命中率
SELECT 
  (1 - Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests) * 100 
  AS buffer_pool_hit_ratio;
```

**评分标准**：
```
命中率 ≥ 99%: 得分 1.0（优秀）
命中率 98-99%: 得分 0.9（良好）
命中率 95-98%: 得分 0.7（可接受）
命中率 90-95%: 得分 0.5（需要优化）
命中率 < 90%: 得分 0.3（严重问题）
```

**优化建议**：
- **目标命中率**：≥ 99%
- **参数调整**：`innodb_buffer_pool_size` 应设置为服务器内存的70-80%
- **监控指标**：关注 `Innodb_buffer_pool_reads`（物理读）应远小于 `Innodb_buffer_pool_read_requests`
- **预热策略**：重启后使用 `innodb_buffer_pool_dump_at_shutdown` 和 `innodb_buffer_pool_load_at_startup` 快速恢复

##### 查询性能得分（6%总权重）

**数据来源**：
- 慢查询日志：`slow_query_log`
- `SHOW GLOBAL STATUS LIKE 'Slow_queries'`
- `SHOW GLOBAL STATUS LIKE 'Questions'`

**计算方法**：
```python
慢查询比率 = Slow_queries / Questions × 100%

查询性能得分计算：
- 慢查询比率 < 0.5%: 得分 1.0
- 慢查询比率 0.5-1%: 得分 0.9
- 慢查询比率 1-3%: 得分 0.7
- 慢查询比率 3-5%: 得分 0.5
- 慢查询比率 > 5%: 得分 0.3
```

**配置建议**：
```ini
# my.cnf 配置
slow_query_log = 1
long_query_time = 2  # 2秒以上记录为慢查询
log_queries_not_using_indexes = 1
```

### 2. 可用性得分（25%权重）

评估系统的服务能力和对外提供服务的质量。

#### 计算公式

```python
可用性得分 = (
    连接成功率 × 0.40 +
    慢查询影响度得分 × 0.30 +
    错误日志严重度得分 × 0.30
)
```

#### 详细指标说明

##### 连接成功率（10%总权重）

**数据来源**：
```sql
SHOW GLOBAL STATUS LIKE 'Aborted_connects';
SHOW GLOBAL STATUS LIKE 'Connections';

连接成功率 = (Connections - Aborted_connects) / Connections × 100%
```

**评分标准**：
```
成功率 = 100%: 得分 1.0
成功率 99-100%: 得分 0.9
成功率 95-99%: 得分 0.6
成功率 < 95%: 得分 0.3
```

**优化措施**：
- 检查网络稳定性
- 调整 `max_connections` 参数
- 使用连接池管理连接
- 排查频繁连接断开的原因

##### 慢查询影响度（7.5%总权重）

综合考虑慢查询的数量、平均执行时间、影响的行数。

**计算方法**：
```python
慢查询影响度 = (
    慢查询数量权重 × 0.40 +
    平均执行时间权重 × 0.35 +
    影响行数权重 × 0.25
)
```

### 3. 稳定性得分（20%权重）

评估系统的稳定性和一致性，关注资源使用波动和异常情况。

#### 计算公式

```python
稳定性得分 = (
    资源波动性得分 × 0.35 +
    锁等待得分 × 0.30 +
    死锁频率得分 × 0.20 +
    主从复制健康度 × 0.15
)
```

#### 关键指标

##### 死锁频率得分（4%总权重）

**数据来源**：
```sql
SHOW ENGINE INNODB STATUS;  -- 查看 LATEST DETECTED DEADLOCK
SHOW GLOBAL STATUS LIKE 'Innodb_deadlocks';  -- MySQL 8.0+
```

**评分标准**：
```
每小时死锁数 = 0: 得分 1.0
每小时死锁数 1-2: 得分 0.9
每小时死锁数 3-5: 得分 0.7
每小时死锁数 6-10: 得分 0.5
每小时死锁数 > 10: 得分 0.3
```

**预防策略**：
- 按相同顺序访问表和行
- 缩短事务长度
- 降低隔离级别（如果业务允许）
- 合理使用索引减少锁范围

##### 主从复制健康度（3%总权重）

**数据来源**：
```sql
SHOW SLAVE STATUS\G

关键指标：
- Seconds_Behind_Master  -- 复制延迟
- Slave_IO_Running       -- IO线程状态
- Slave_SQL_Running      -- SQL线程状态
- Last_Error             -- 最后错误
```

**评分标准**：
```python
基础分数 = 1.0

# 状态检查
if Slave_IO_Running != 'Yes': 基础分数 = 0
if Slave_SQL_Running != 'Yes': 基础分数 = 0

# 延迟评分（仅当线程正常时）
if 基础分数 > 0:
    if Seconds_Behind_Master == 0: 得分 1.0
    elif Seconds_Behind_Master <= 5: 得分 0.9
    elif Seconds_Behind_Master <= 30: 得分 0.7
    elif Seconds_Behind_Master <= 60: 得分 0.5
    else: 得分 0.3
```

### 4. 容量得分（10%权重）

评估资源的剩余容量和扩展空间。

#### 计算公式

```python
容量得分 = (
    存储空间余量得分 × 0.40 +
    连接池使用率得分 × 0.35 +
    临时表空间使用得分 × 0.25
)
```

#### 存储空间余量（4%总权重）

**数据来源**：
- 文件系统监控：`df -h`
- MySQL数据目录大小：`du -sh /var/lib/mysql`

**评分标准**：
```
余量 > 40%: 得分 1.0（充足）
余量 30-40%: 得分 0.9（良好）
余量 20-30%: 得分 0.7（需关注）
余量 10-20%: 得分 0.5（警告）
余量 5-10%: 得分 0.3（危险）
余量 < 5%: 得分 0.1（严重）
```

**容量规划**：
- 当余量 < 30%时，开始制定扩容计划
- 当余量 < 20%时，执行扩容操作
- 定期清理不需要的binlog、slow_log
- 使用分区表管理大表数据

### 5. 存储引擎健康度（5%权重）

专注于InnoDB存储引擎的健康状况。

#### 计算公式

```python
存储引擎健康度 = (
    InnoDB状态得分 × 0.60 +
    表碎片率得分 × 0.40
)
```

#### 表碎片率评估

**数据来源**：
```sql
SELECT 
  table_schema,
  table_name,
  (data_free / (data_length + index_length)) * 100 AS fragmentation_ratio
FROM information_schema.TABLES
WHERE engine = 'InnoDB'
  AND data_length > 0
ORDER BY fragmentation_ratio DESC;
```

**优化方法**：
```sql
-- 优化表以减少碎片
OPTIMIZE TABLE table_name;

-- 或者使用
ALTER TABLE table_name ENGINE=InnoDB;
```

---

## MySQL 健康度影响因素矩阵

| 指标项 | 维度 | 权重 | 正常阈值 | 警告阈值 | 危险阈值 | 数据来源 | 获取频率 |
|--------|------|------|----------|----------|----------|----------|----------|
| CPU使用率 | 性能 | 12% | < 60% | 60-80% | > 80% | SHOW STATUS, OS监控 | 30秒 |
| InnoDB缓冲池命中率 | 性能 | 8% | ≥ 99% | 95-99% | < 95% | SHOW STATUS | 5分钟 |
| 查询响应时间(P95) | 性能 | 6% | < 100ms | 100-500ms | > 500ms | slow_query_log | 5分钟 |
| 慢查询比率 | 可用性 | 7.5% | < 0.5% | 0.5-3% | > 5% | SHOW STATUS | 5分钟 |
| 连接成功率 | 可用性 | 10% | 100% | 99-100% | < 99% | SHOW STATUS | 1分钟 |
| 死锁频率(/小时) | 稳定性 | 4% | 0 | 1-5 | > 10 | SHOW ENGINE INNODB STATUS | 5分钟 |
| 复制延迟(秒) | 稳定性 | 3% | 0 | 1-30 | > 60 | SHOW SLAVE STATUS | 30秒 |
| 表锁等待比率 | 稳定性 | 6% | < 0.1% | 0.1-1% | > 1% | SHOW STATUS | 5分钟 |
| 存储余量 | 容量 | 4% | > 30% | 20-30% | < 10% | df -h | 1小时 |
| 连接池使用率 | 容量 | 3.5% | < 70% | 70-85% | > 90% | SHOW STATUS | 30秒 |
| 临时表创建率 | 容量 | 2.5% | < 10/s | 10-50/s | > 100/s | SHOW STATUS | 5分钟 |
| 表碎片率 | 存储引擎 | 2% | < 10% | 10-20% | > 30% | information_schema.TABLES | 24小时 |

---

## PostgreSQL 健康度计算模型

### 整体计算公式

```python
PostgreSQL健康度 = (
    性能得分 × 0.40 +
    可用性得分 × 0.25 +
    稳定性得分 × 0.20 +
    容量得分 × 0.10 +
    维护健康度 × 0.05
) × 100
```

### 1. 性能得分（40%权重）

#### 计算公式

```python
性能得分 = (
    CPU得分 × 0.30 +
    缓冲区命中率得分 × 0.25 +
    查询性能得分 × 0.20 +
    WAL性能得分 × 0.15 +
    IO性能得分 × 0.10
)
```

#### 缓冲区命中率（PostgreSQL核心指标）

**数据来源**：
```sql
SELECT 
  sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0) * 100 AS buffer_hit_ratio
FROM pg_stat_database;
```

**评分标准**：
```
命中率 ≥ 99%: 得分 1.0（优秀）
命中率 98-99%: 得分 0.9（良好）
命中率 95-98%: 得分 0.7（可接受）
命中率 90-95%: 得分 0.5（需要优化）
命中率 < 90%: 得分 0.3（严重问题）
```

**配置优化**：
```postgresql
-- postgresql.conf
shared_buffers = 8GB              -- 建议为系统内存的25%
effective_cache_size = 24GB        -- 建议为系统内存的75%
```

**业界最佳实践**：
- PostgreSQL的缓冲区命中率目标应 ≥ 99%
- `shared_buffers` 设置为系统内存的25%（不超过8GB）
- `effective_cache_size` 设置为系统内存的75%，用于查询优化器成本估算

#### WAL性能得分（6%总权重）

**数据来源**（PostgreSQL 14+）：
```sql
SELECT * FROM pg_stat_wal;

-- 关键指标
SELECT 
  wal_records,           -- WAL记录数
  wal_fpi,              -- Full Page Images数量
  wal_bytes,            -- WAL写入字节数
  wal_buffers_full,     -- WAL缓冲区满的次数
  wal_write,            -- WAL写入次数
  wal_sync              -- WAL同步次数
FROM pg_stat_wal;
```

**评分标准**：
```python
WAL性能得分 = (
    WAL缓冲区健康度 × 0.50 +
    WAL写入效率 × 0.30 +
    Checkpoint频率合理性 × 0.20
)

WAL缓冲区健康度：
- wal_buffers_full = 0: 得分 1.0
- wal_buffers_full < 100/小时: 得分 0.8
- wal_buffers_full > 1000/小时: 得分 0.3
```

**优化建议**：
```postgresql
-- postgresql.conf
wal_buffers = 16MB                 -- WAL缓冲区大小
max_wal_size = 4GB                 -- 最大WAL大小
checkpoint_completion_target = 0.9 -- Checkpoint完成目标
```

### 2. 维护健康度（5%权重 - PostgreSQL特色）

这是PostgreSQL独有的重要维度，反映数据库维护任务的执行情况。

#### 计算公式

```python
维护健康度 = (
    表膨胀率得分 × 0.40 +
    死元组比率得分 × 0.30 +
    AutoVacuum效率得分 × 0.20 +
    统计信息新鲜度得分 × 0.10
)
```

#### 表膨胀率（PostgreSQL关键问题）

**数据来源**：
```sql
SELECT 
  schemaname,
  tablename,
  n_live_tup,
  n_dead_tup,
  CASE 
    WHEN n_live_tup > 0 
    THEN round((n_dead_tup::numeric / n_live_tup::numeric) * 100, 2)
    ELSE 0 
  END AS dead_tuple_ratio,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

**膨胀率定义**：
```
表膨胀率 = (实际物理大小 / 理论最小大小) 

简化计算：
死元组比率 = n_dead_tup / (n_live_tup + n_dead_tup) × 100%
```

**评分标准**：
```
死元组比率 < 5%: 得分 1.0（优秀）
死元组比率 5-10%: 得分 0.8（良好）
死元组比率 10-20%: 得分 0.5（警告）
死元组比率 20-30%: 得分 0.3（危险）
死元组比率 > 30%: 得分 0.1（严重）
```

**为什么表膨胀严重？**
1. **UPDATE/DELETE频繁**：PostgreSQL的MVCC机制会产生死元组
2. **AutoVacuum不及时**：配置不当导致清理延迟
3. **长事务阻塞**：长时间运行的事务阻止VACUUM清理
4. **AutoVacuum被取消**：手动操作或配置导致VACUUM无法完成

**优化策略**：
```postgresql
-- postgresql.conf 优化配置
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 30s                          -- 缩短检查间隔
autovacuum_vacuum_scale_factor = 0.05             -- 降低阈值，更频繁清理
autovacuum_analyze_scale_factor = 0.05
autovacuum_vacuum_cost_limit = 2000               -- 提高VACUUM优先级

-- 针对高频更新表的特殊配置
ALTER TABLE high_update_table 
SET (autovacuum_vacuum_scale_factor = 0.01);

-- 手动VACUUM策略
VACUUM (VERBOSE, ANALYZE) table_name;             -- 常规清理
VACUUM FULL table_name;                           -- 完全清理（需要锁表）
```

#### AutoVacuum效率评估

**评分标准**：
```python
AutoVacuum效率得分计算：

对于每个表：
  最近一次VACUUM距今时间 = now() - last_autovacuum
  
  if 最近一次VACUUM距今 < 1小时: 得分 1.0
  elif 最近一次VACUUM距今 < 6小时: 得分 0.8
  elif 最近一次VACUUM距今 < 24小时: 得分 0.6
  elif 最近一次VACUUM距今 < 72小时: 得分 0.4
  else: 得分 0.2

整体效率 = 所有表得分的加权平均（按表大小加权）
```

**监控查询**：
```sql
-- 查找长时间未VACUUM的表
SELECT 
  schemaname,
  tablename,
  last_autovacuum,
  last_vacuum,
  now() - COALESCE(last_autovacuum, last_vacuum, '1970-01-01'::timestamp) AS vacuum_age,
  n_dead_tup,
  n_live_tup
FROM pg_stat_user_tables
WHERE n_live_tup > 1000  -- 过滤小表
ORDER BY vacuum_age DESC NULLS FIRST
LIMIT 20;
```

---

## PostgreSQL 健康度影响因素矩阵

| 指标项 | 维度 | 权重 | 正常阈值 | 警告阈值 | 危险阈值 | 数据来源 | 获取频率 |
|--------|------|------|----------|----------|----------|----------|----------|
| 缓冲区命中率 | 性能 | 10% | ≥ 99% | 95-99% | < 95% | pg_stat_database | 5分钟 |
| WAL缓冲区满次数 | 性能 | 4.5% | 0 | < 100/h | > 1000/h | pg_stat_wal | 5分钟 |
| 死元组比率 | 维护 | 1.5% | < 5% | 5-10% | > 20% | pg_stat_user_tables | 10分钟 |
| AutoVacuum延迟 | 维护 | 1% | < 1h | 1-6h | > 24h | pg_stat_user_tables | 10分钟 |
| 表膨胀率 | 维护 | 2% | < 1.2 | 1.2-1.5 | > 2.0 | pg_stat_user_tables | 1小时 |
| 临时文件创建 | 容量 | 2.5% | < 100/h | 100-1000/h | > 1000/h | pg_stat_database | 5分钟 |
| 锁等待数 | 稳定性 | 6% | 0 | 1-5 | > 10 | pg_locks | 1分钟 |
| 连接数 | 可用性 | 10% | < 70% | 70-85% | > 90% | pg_stat_activity | 30秒 |

---

## OceanBase 健康度计算模型

### 整体计算公式

```python
OceanBase健康度 = (
    性能得分 × 0.35 +
    可用性得分 × 0.25 +
    稳定性得分 × 0.20 +
    资源管理得分 × 0.15 +
    分布式一致性得分 × 0.05
) × 100
```

### 1. 性能得分（35%权重）

#### 计算公式

```python
性能得分 = (
    租户资源使用得分 × 0.30 +
    计划缓存命中率得分 × 0.25 +
    RPC性能得分 × 0.20 +
    查询性能得分 × 0.15 +
    MemStore效率得分 × 0.10
)
```

#### 计划缓存命中率（OceanBase核心指标）

**数据来源**：
```sql
SELECT 
  tenant_id,
  svr_ip,
  svr_port,
  hit_count,
  miss_count,
  (hit_count / NULLIF(hit_count + miss_count, 0)) * 100 AS hit_ratio
FROM GV$OB_PLAN_CACHE_STAT
ORDER BY hit_ratio ASC;
```

**评分标准**：
```
命中率 ≥ 98%: 得分 1.0（优秀）
命中率 95-98%: 得分 0.9（良好）
命中率 90-95%: 得分 0.7（可接受）
命中率 85-90%: 得分 0.5（需要优化）
命中率 < 85%: 得分 0.3（严重问题）
```

**优化建议**：
```sql
-- 调整计划缓存内存大小
ALTER SYSTEM SET plan_cache_mem_limit = '2G';

-- 查看计划缓存使用情况
SELECT 
  tenant_name,
  mem_limit / 1024 / 1024 / 1024 AS mem_limit_gb,
  mem_used / 1024 / 1024 / 1024 AS mem_used_gb
FROM GV$OB_PLAN_CACHE_STAT;
```

**业界最佳实践**：
- 计划缓存命中率应保持 ≥ 95%
- `plan_cache_mem_limit` 建议设置为租户内存的3-5%
- 高并发OLTP场景，应达到98%以上

#### RPC性能得分（7%总权重）

**数据来源**：
```sql
-- RPC统计信息
SELECT 
  tenant_id,
  svr_ip,
  queue_len AS rpc_queue_length,
  delay_us / 1000 AS delay_ms
FROM GV$OB_RPC_OUTGOING
WHERE tenant_id = 1001  -- 指定租户
ORDER BY queue_len DESC;
```

**评分标准**：
```
RPC队列长度 = 0: 得分 1.0（优秀）
RPC队列长度 1-5: 得分 0.9（良好）
RPC队列长度 6-10: 得分 0.7（可接受）
RPC队列长度 11-50: 得分 0.5（警告）
RPC队列长度 > 50: 得分 0.2（严重）
```

**影响分析**：
- RPC队列积压表示服务端处理能力不足
- 可能原因：CPU瓶颈、网络延迟、SQL执行慢
- 持续队列积压会导致请求超时

### 2. 资源管理得分（15%权重 - OceanBase特色）

OceanBase采用多租户架构，资源管理是核心能力。

#### 计算公式

```python
资源管理得分 = (
    租户内存使用率得分 × 0.40 +
    MemStore使用率得分 × 0.30 +
    日志盘使用率得分 × 0.20 +
    Tablet分布均衡度得分 × 0.10
)
```

#### MemStore使用率（OceanBase独特机制）

**数据来源**：
```sql
SELECT 
  tenant_id,
  svr_ip,
  active_memstore_used / 1024 / 1024 AS active_mb,
  freeze_trigger / 1024 / 1024 AS freeze_trigger_mb,
  (active_memstore_used::FLOAT / NULLIF(freeze_trigger, 0)) * 100 AS usage_ratio
FROM GV$OB_MEMSTORE
ORDER BY usage_ratio DESC;
```

**MemStore机制说明**：
- **MemStore**：OceanBase的内存写缓冲区
- **冻结（Freeze）**：当MemStore达到阈值，触发冻结，转为只读
- **转储（Dump）**：将冻结的MemStore持久化到SSTable
- **影响**：频繁冻结会影响写入性能

**评分标准**：
```
使用率 < 60%: 得分 1.0（健康）
使用率 60-70%: 得分 0.9（正常）
使用率 70-80%: 得分 0.7（关注）
使用率 80-90%: 得分 0.5（警告，可能触发冻结）
使用率 90-95%: 得分 0.3（危险，即将冻结）
使用率 > 95%: 得分 0.1（严重，正在/已冻结）
```

**优化配置**：
```sql
-- 调整MemStore大小
ALTER SYSTEM SET memstore_limit_percentage = 60;  -- MemStore占租户内存的比例

-- 调整冻结阈值
ALTER SYSTEM SET freeze_trigger_percentage = 70;  -- 触发冻结的阈值

-- 加速转储
ALTER SYSTEM SET minor_merge_concurrency = 4;     -- 并发转储线程数
```

#### 合并（Compaction）状态

**数据来源**：
```sql
-- Major Compaction 进度
SELECT 
  zone,
  broadcast_scn,
  last_scn,
  status,
  is_error
FROM CDB_OB_MAJOR_COMPACTION;

-- Minor Compaction 统计
SELECT 
  tenant_id,
  COUNT(*) AS pending_minor_compactions
FROM GV$OB_COMPACTION_PROGRESS
WHERE type = 'MINOR'
  AND status != 'FINISH'
GROUP BY tenant_id;
```

**合并类型说明**：
- **Minor Compaction**：增量合并，将MemStore转储的SSTable合并
- **Major Compaction**：全量合并，清理历史版本，回收空间

**评分标准**：
```python
合并状态得分 = (
    Major合并健康度 × 0.60 +
    Minor合并健康度 × 0.40
)

Major合并健康度：
- 合并已完成: 得分 1.0
- 合并进行中(< 2小时): 得分 0.9
- 合并进行中(2-6小时): 得分 0.7
- 合并进行中(> 6小时): 得分 0.5
- 合并失败: 得分 0.2

Minor合并健康度：
- 待处理数 < 20: 得分 1.0
- 待处理数 20-50: 得分 0.8
- 待处理数 50-100: 得分 0.6
- 待处理数 > 100: 得分 0.3
```

**最佳实践**：
- Major Compaction应在业务低峰期执行（凌晨2-6点）
- 通过 `major_freeze_duty_time` 控制执行时间窗口
- 监控合并进度，避免长时间未完成

### 3. 分布式一致性得分（5%权重 - OceanBase特有）

评估分布式架构下的数据一致性和高可用能力。

#### 计算公式

```python
分布式一致性得分 = (
    副本同步状态得分 × 0.50 +
    Paxos日志同步延迟得分 × 0.30 +
    Leader分布均衡度得分 × 0.20
)
```

#### 副本同步状态

**数据来源**：
```sql
-- 查看副本状态
SELECT 
  tenant_id,
  table_id,
  partition_id,
  svr_ip,
  role,  -- LEADER/FOLLOWER
  replica_type,  -- FULL/LOGONLY
  status,
  data_size / 1024 / 1024 AS data_size_mb
FROM CDB_OB_TABLE_LOCATIONS
WHERE tenant_id = 1001
ORDER BY table_id, partition_id;
```

**评分标准**：
```
所有副本状态正常: 得分 1.0
存在副本延迟 < 1秒: 得分 0.9
存在副本延迟 1-5秒: 得分 0.7
存在副本不可用: 得分 0.3
```

---

## OceanBase 健康度影响因素矩阵

| 指标项 | 维度 | 权重 | 正常阈值 | 警告阈值 | 危险阈值 | 数据来源 | 获取频率 |
|--------|------|------|----------|----------|----------|----------|----------|
| 计划缓存命中率 | 性能 | 8.75% | ≥ 98% | 95-98% | < 90% | GV$OB_PLAN_CACHE_STAT | 5分钟 |
| RPC队列长度 | 性能 | 7% | 0-5 | 6-10 | > 50 | GV$OB_RPC_OUTGOING | 30秒 |
| MemStore使用率 | 资源 | 4.5% | < 60% | 60-80% | > 90% | GV$OB_MEMSTORE | 1分钟 |
| 租户内存使用率 | 资源 | 6% | < 70% | 70-85% | > 90% | GV$OB_TENANT | 1分钟 |
| Minor合并待处理 | 资源 | 3% | < 20 | 20-50 | > 100 | GV$OB_COMPACTION_PROGRESS | 5分钟 |
| Major合并进度 | 资源 | 3% | 已完成 | 进行中 | 超时 | CDB_OB_MAJOR_COMPACTION | 10分钟 |
| 日志盘使用率 | 容量 | 3% | < 70% | 70-85% | > 90% | 系统监控 | 10分钟 |
| 副本同步延迟 | 一致性 | 2.5% | 0 | < 1s | > 5s | CDB_OB_TABLE_LOCATIONS | 30秒 |
| Tablet数量 | 资源 | 1.5% | < 10万 | 10-50万 | > 100万 | 系统表 | 1小时 |

---

## 健康度计算实现细节

### 数据采集策略

#### 采集周期分类

```python
采集周期 = {
    "实时指标": {
        "周期": 30秒,
        "指标": ["CPU使用率", "内存使用率", "连接数", "RPC队列长度"],
        "目的": "快速发现突发问题"
    },
    "准实时指标": {
        "周期": 5分钟,
        "指标": ["缓存命中率", "慢查询统计", "锁等待", "死锁数"],
        "目的": "性能趋势分析"
    },
    "定期指标": {
        "周期": 1小时,
        "指标": ["表统计信息", "膨胀率", "碎片率", "AutoVacuum"],
        "目的": "维护状态评估"
    },
    "低频指标": {
        "周期": 24小时,
        "指标": ["表大小增长", "索引使用率", "分区策略"],
        "目的": "容量规划"
    }
}
```

### 异常值处理

#### 数据缺失处理

```python
def handle_missing_data(metric_name, historical_data):
    """处理指标数据缺失"""
    if 数据缺失原因 == "采集失败":
        # 使用最近一次有效值
        return 最近有效值
    elif 数据缺失原因 == "新实例":
        # 使用保守估计
        return 默认安全值
    elif 历史数据充足:
        # 使用历史平均值
        return calculate_moving_average(historical_data, window=10)
    else:
        # 降低该指标权重
        return None, 权重调整=0.5
```

#### 异常波动平滑

```python
def smooth_metric(current_value, historical_values, threshold=0.3):
    """平滑处理异常波动"""
    moving_avg = calculate_moving_average(historical_values, window=5)
    
    # 检测异常波动
    deviation = abs(current_value - moving_avg) / moving_avg
    
    if deviation > threshold:
        # 异常波动，使用加权平均
        return current_value * 0.7 + moving_avg * 0.3
    else:
        return current_value
```

### 新实例引导期

新创建的数据库实例前24小时使用简化评分模型：

```python
def calculate_new_instance_health(metrics, instance_age_hours):
    """新实例健康度计算"""
    if instance_age_hours < 1:
        # 仅评估基础可用性
        return calculate_basic_availability(metrics)
    elif instance_age_hours < 6:
        # 逐步增加评估维度
        weight = instance_age_hours / 24.0
        return (
            calculate_full_health(metrics) * weight +
            calculate_basic_availability(metrics) * (1 - weight)
        )
    else:
        # 使用完整模型
        return calculate_full_health(metrics)
```

### 权重动态调整

支持根据业务场景自定义权重：

```python
# 预设场景配置
SCENARIO_WEIGHTS = {
    "高并发OLTP": {
        "performance": 0.50,  # 提高性能权重
        "availability": 0.30,
        "stability": 0.15,
        "capacity": 0.04,
        "maintenance": 0.01
    },
    "数据仓库": {
        "performance": 0.35,
        "availability": 0.20,
        "stability": 0.15,
        "capacity": 0.20,  # 提高容量权重
        "maintenance": 0.10
    },
    "读密集型": {
        "performance": 0.45,
        "availability": 0.30,
        "stability": 0.15,
        "capacity": 0.07,
        "maintenance": 0.03
    }
}

# 应用自定义权重
def apply_custom_weights(database_type, scenario):
    """应用场景化权重配置"""
    base_weights = get_default_weights(database_type)
    scenario_weights = SCENARIO_WEIGHTS.get(scenario, {})
    
    return {**base_weights, **scenario_weights}
```

---

## 健康度可视化与告警

### 可视化展示

#### 1. 综合健康度仪表盘

```javascript
// 环形进度条展示
<CircleProgress 
  percent={healthScore}
  strokeColor={getHealthColor(healthScore)}
  format={() => `${healthScore}\n健康度`}
/>

// 颜色映射
function getHealthColor(score) {
  if (score >= 90) return '#52c41a';  // 绿色
  if (score >= 75) return '#faad14';  // 黄色
  if (score >= 60) return '#fa8c16';  // 橙色
  return '#f5222d';                    // 红色
}
```

#### 2. 维度雷达图

```javascript
// 展示各维度得分对比
<Radar
  data={[
    { dimension: '性能', score: 85 },
    { dimension: '可用性', score: 92 },
    { dimension: '稳定性', score: 78 },
    { dimension: '容量', score: 88 },
    { dimension: '维护', score: 75 }
  ]}
  angleField="dimension"
  radiusField="score"
  max={100}
/>
```

#### 3. 健康度趋势图

```javascript
// 显示过去7天的健康度变化
<Line
  data={healthScoreHistory}
  xField="timestamp"
  yField="healthScore"
  yAxis={{ min: 0, max: 100 }}
  annotations={[
    { type: 'line', start: ['min', 90], end: ['max', 90], text: '优秀' },
    { type: 'line', start: ['min', 75], end: ['max', 75], text: '良好' },
    { type: 'line', start: ['min', 60], end: ['max', 60], text: '警告' }
  ]}
/>
```

### 健康度报告

系统自动生成健康度分析报告：

```markdown
## 数据库健康度报告

**实例**: MySQL-生产环境-01
**评估时间**: 2025-10-04 14:30:00
**综合评分**: 78分（良好）

### 维度得分明细

| 维度 | 得分 | 状态 | 影响权重 |
|------|------|------|----------|
| 性能 | 72 | ⚠️ 警告 | 40% |
| 可用性 | 88 | ✅ 良好 | 25% |
| 稳定性 | 81 | ✅ 良好 | 20% |
| 容量 | 75 | 🟡 关注 | 10% |
| 存储引擎 | 85 | ✅ 良好 | 5% |

### 影响健康度的主要因素 (Top 5)

1. **InnoDB缓冲池命中率偏低** (影响: -8分)
   - 当前值: 94.2%
   - 目标值: ≥ 99%
   - 建议: 增加 `innodb_buffer_pool_size` 从 2G 到 6G

2. **慢查询比率较高** (影响: -5分)
   - 当前值: 3.2%
   - 目标值: < 1%
   - 建议: 优化Top 10慢查询，添加适当索引

3. **CPU使用率波动较大** (影响: -4分)
   - 当前值: 峰值82%
   - 建议: 优化高CPU查询，考虑读写分离

4. **连接池使用率接近上限** (影响: -3分)
   - 当前值: 85%
   - 建议: 增加 `max_connections` 或使用连接池

5. **表碎片率偏高** (影响: -2分)
   - 影响表数: 5个大表
   - 建议: 对大表执行 OPTIMIZE TABLE

### 优化建议

#### 立即执行（24小时内）
- [ ] 增加InnoDB缓冲池大小至6GB
- [ ] 优化Top 3慢查询

#### 近期计划（1周内）
- [ ] 调整连接池配置
- [ ] 对5个大表执行OPTIMIZE TABLE
- [ ] 开启查询缓存监控

#### 长期规划
- [ ] 考虑读写分离架构
- [ ] 制定容量扩容计划
- [ ] 建立自动化优化流程
```

### 告警规则

```python
# 健康度告警配置
HEALTH_ALERT_RULES = {
    "critical": {
        "condition": "health_score < 60",
        "alert_level": "P1",
        "notification": ["SMS", "电话", "邮件"],
        "message": "数据库健康度严重下降，当前{score}分，请立即处理！"
    },
    "warning": {
        "condition": "health_score < 75 for 1 hour",
        "alert_level": "P2",
        "notification": ["邮件", "企业微信"],
        "message": "数据库健康度持续低于75分，当前{score}分"
    },
    "trend": {
        "condition": "health_score drop > 15 in 24 hours",
        "alert_level": "P2",
        "notification": ["邮件"],
        "message": "健康度24小时内下降{drop}分，从{old}降至{new}"
    },
    "dimension": {
        "condition": "dimension_score < 0.5",
        "alert_level": "P3",
        "notification": ["邮件"],
        "message": "{dimension}维度得分过低({score})，需要关注"
    }
}
```

---

## 健康度优化实战

### 快速提升健康度 - 行动清单

#### MySQL 优化检查清单（按影响力排序）

**Level 1: 高影响优化（预期提升10-20分）**

- [ ] **优化InnoDB缓冲池**
  ```sql
  -- 检查当前配置
  SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
  
  -- 建议配置（系统内存的70-80%）
  SET GLOBAL innodb_buffer_pool_size = 6442450944; -- 6GB
  
  -- 动态调整无需重启（MySQL 5.7.5+）
  ```

- [ ] **处理慢查询**
  ```sql
  -- 查看Top 10慢查询
  SELECT 
    query_time, lock_time, rows_sent, rows_examined,
    sql_text
  FROM mysql.slow_log
  ORDER BY query_time DESC
  LIMIT 10;
  
  -- 使用EXPLAIN分析
  EXPLAIN SELECT ...;
  
  -- 添加必要索引
  ALTER TABLE table_name ADD INDEX idx_column (column);
  ```

- [ ] **优化连接配置**
  ```sql
  -- 检查连接使用情况
  SHOW STATUS LIKE 'Threads%';
  SHOW STATUS LIKE 'Max_used_connections';
  
  -- 调整max_connections
  SET GLOBAL max_connections = 1000;
  
  -- 配置连接超时
  SET GLOBAL wait_timeout = 600;
  SET GLOBAL interactive_timeout = 600;
  ```

**Level 2: 中等影响优化（预期提升5-10分）**

- [ ] **优化表碎片**
  ```sql
  -- 查找碎片率高的表
  SELECT 
    table_schema,
    table_name,
    (data_free / (data_length + index_length)) * 100 AS frag_ratio
  FROM information_schema.TABLES
  WHERE table_schema NOT IN ('mysql', 'information_schema', 'performance_schema')
    AND data_length > 0
  ORDER BY frag_ratio DESC
  LIMIT 20;
  
  -- 优化表（业务低峰期执行）
  OPTIMIZE TABLE table_name;
  ```

- [ ] **处理死锁和锁等待**
  ```sql
  -- 查看当前锁等待
  SELECT * FROM information_schema.INNODB_LOCKS;
  SELECT * FROM information_schema.INNODB_LOCK_WAITS;
  
  -- 查看事务状态
  SELECT * FROM information_schema.INNODB_TRX;
  
  -- 杀掉长时间运行的事务
  KILL transaction_id;
  ```

#### PostgreSQL 优化检查清单

**Level 1: 高影响优化**

- [ ] **处理表膨胀**
  ```sql
  -- 查找膨胀严重的表
  SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    round((n_dead_tup::numeric / NULLIF(n_live_tup, 0)::numeric) * 100, 2) AS dead_ratio
  FROM pg_stat_user_tables
  WHERE n_live_tup > 1000
  ORDER BY n_dead_tup DESC
  LIMIT 20;
  
  -- 手动VACUUM
  VACUUM (VERBOSE, ANALYZE) table_name;
  
  -- 如果膨胀严重（业务低峰期）
  VACUUM FULL table_name;  -- 注意：需要锁表
  ```

- [ ] **优化AutoVacuum配置**
  ```postgresql
  -- postgresql.conf
  autovacuum = on
  autovacuum_max_workers = 4
  autovacuum_naptime = 30s
  autovacuum_vacuum_scale_factor = 0.05
  autovacuum_analyze_scale_factor = 0.05
  
  -- 针对高频更新表
  ALTER TABLE high_update_table 
  SET (autovacuum_vacuum_scale_factor = 0.01);
  ```

- [ ] **优化缓冲区命中率**
  ```postgresql
  -- 检查命中率
  SELECT 
    sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0) * 100 AS hit_ratio
  FROM pg_stat_database;
  
  -- postgresql.conf 优化
  shared_buffers = 8GB          -- 系统内存的25%
  effective_cache_size = 24GB   -- 系统内存的75%
  ```

#### OceanBase 优化检查清单

**Level 1: 高影响优化**

- [ ] **优化计划缓存**
  ```sql
  -- 检查命中率
  SELECT 
    (hit_count / NULLIF(hit_count + miss_count, 0)) * 100 AS hit_ratio
  FROM GV$OB_PLAN_CACHE_STAT;
  
  -- 调整缓存大小
  ALTER SYSTEM SET plan_cache_mem_limit = '2G';
  ```

- [ ] **处理MemStore压力**
  ```sql
  -- 检查MemStore使用率
  SELECT 
    (active_memstore_used::FLOAT / NULLIF(freeze_trigger, 0)) * 100 AS usage_ratio
  FROM GV$OB_MEMSTORE;
  
  -- 优化配置
  ALTER SYSTEM SET memstore_limit_percentage = 60;
  ALTER SYSTEM SET freeze_trigger_percentage = 70;
  ```

- [ ] **加速合并进度**
  ```sql
  -- 检查Minor合并积压
  SELECT COUNT(*) AS pending_count
  FROM GV$OB_COMPACTION_PROGRESS
  WHERE type = 'MINOR' AND status != 'FINISH';
  
  -- 加速合并
  ALTER SYSTEM SET minor_merge_concurrency = 4;
  
  -- 手动触发Major合并（业务低峰期）
  ALTER SYSTEM MAJOR FREEZE;
  ```

### 长期健康度维护策略

#### 1. 建立性能基线

```python
# 记录正常业务期间的性能基线
PERFORMANCE_BASELINE = {
    "cpu_usage": {"normal": 45, "peak": 65},
    "memory_usage": {"normal": 60, "peak": 75},
    "qps": {"normal": 2000, "peak": 5000},
    "cache_hit_ratio": {"min": 98},
    "slow_query_ratio": {"max": 0.5}
}

# 基线偏离告警
if current_metric > baseline * 1.5:
    alert("性能指标超出基线50%")
```

#### 2. 定期维护任务

```python
# 维护任务时间表
MAINTENANCE_SCHEDULE = {
    "每日": [
        "检查慢查询Top 10",
        "检查错误日志",
        "检查磁盘空间",
        "验证备份完成"
    ],
    "每周": [
        "分析表统计信息（ANALYZE）",
        "检查索引使用率",
        "清理过期binlog",
        "审查健康度报告"
    ],
    "每月": [
        "执行表优化（OPTIMIZE）",
        "审查慢查询趋势",
        "容量规划评估",
        "配置参数审查"
    ]
}
```

#### 3. 健康度目标设定

```python
# 不同环境的健康度目标
HEALTH_SCORE_TARGETS = {
    "生产环境": {
        "target": 85,
        "minimum": 75,
        "alert_threshold": 70
    },
    "测试环境": {
        "target": 75,
        "minimum": 60,
        "alert_threshold": 55
    },
    "开发环境": {
        "target": 70,
        "minimum": 60,
        "alert_threshold": 50
    }
}
```

---

## 总结

健康度指标体系是数据库性能管理的核心工具，通过：

- ✅ **量化评估**：将复杂的数据库状态转化为简单的分数
- ✅ **趋势分析**：通过历史健康度识别性能退化
- ✅ **精准定位**：明确指出影响健康度的关键因素
- ✅ **指导优化**：提供具体的、可操作的优化建议

**使用建议**：
1. 定期查看健康度趋势，而不仅仅关注当前分数
2. 优先优化高权重、低分数的维度
3. 建立自己的性能基线和健康度目标
4. 将健康度作为容量规划和系统演进的参考依据

**记住**：健康度是一个综合指标，单一指标的波动不必过分担心，应关注整体趋势和关键维度。
