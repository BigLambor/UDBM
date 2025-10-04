# OceanBase 性能指标详解

## 概述

OceanBase是阿里巴巴完全自主研发的金融级分布式关系数据库，具有高可用、高性能、水平扩展等特性。作为原生分布式数据库，OceanBase有许多独特的架构设计和性能指标。

本文档详细介绍OceanBase的核心性能指标、监控方法和优化策略，帮助您全面掌握OceanBase性能调优。

---

## OceanBase 架构概述

在学习性能指标前,先理解OceanBase的核心概念：

### 核心架构组件
- **Zone**: 数据中心/机房的逻辑抽象
- **Server (OBServer)**: 数据库服务器节点
- **Tenant (租户)**: 资源隔离的逻辑实例
- **Tablet**: 数据分片的基本单位
- **Leader/Follower**: 副本角色（基于Paxos协议）

### 存储架构
- **MemStore**: 内存增量数据
- **SSTable**: 磁盘基线数据
- **Major Compaction**: 全量合并
- **Minor Compaction**: 增量合并

---

## 核心性能指标

### 1. 计划缓存命中率（Plan Cache Hit Ratio）

#### 指标说明
计划缓存命中率是OceanBase最重要的性能指标之一。SQL执行计划的生成是CPU密集型操作，计划缓存可以避免重复生成执行计划，显著提升性能。

#### 数据来源
```sql
-- 查看计划缓存统计
SELECT 
  tenant_id,
  svr_ip,
  svr_port,
  hit_count,
  miss_count,
  ROUND((hit_count / NULLIF(hit_count + miss_count, 0)) * 100, 2) AS hit_ratio,
  mem_used / 1024 / 1024 AS mem_used_mb,
  mem_limit / 1024 / 1024 AS mem_limit_mb
FROM oceanbase.GV$OB_PLAN_CACHE_STAT
ORDER BY tenant_id, svr_ip;

-- 查看整体命中率
SELECT 
  SUM(hit_count) AS total_hits,
  SUM(miss_count) AS total_misses,
  ROUND(
    (SUM(hit_count)::DECIMAL / NULLIF(SUM(hit_count + miss_count), 0)) * 100,
    2
  ) AS overall_hit_ratio
FROM oceanbase.GV$OB_PLAN_CACHE_STAT
WHERE tenant_id = 1001;  -- 指定租户ID
```

#### 查看计划缓存内容
```sql
-- 查看缓存的SQL
SELECT 
  tenant_id,
  db_id,
  LEFT(query_sql, 100) AS sql_preview,
  hit_count,
  plan_size / 1024 AS plan_size_kb,
  first_load_time,
  last_active_time
FROM oceanbase.GV$OB_PLAN_CACHE_PLAN_STAT
WHERE tenant_id = 1001
ORDER BY hit_count DESC
LIMIT 20;
```

#### 健康阈值
| 状态 | 命中率 | 说明 | 健康度影响 |
|------|--------|------|------------|
| 🟢 优秀 | ≥ 98% | 计划缓存效果理想 | 满分 |
| 🟡 良好 | 95-98% | 正常，有优化空间 | -5分 |
| 🟠 警告 | 90-95% | 需要调整配置 | -10分 |
| 🔴 危险 | < 90% | 严重性能问题 | -20分 |

#### 优化建议

**1. 调整计划缓存内存大小**
```sql
-- 查看当前配置
SHOW PARAMETERS LIKE '%plan_cache%';

-- 租户级别调整
ALTER SYSTEM SET plan_cache_mem_limit = '2G' TENANT = tenant_name;

-- 集群级别调整
ALTER SYSTEM SET plan_cache_mem_limit = '2G';
```

**配置建议**：
- plan_cache_mem_limit 建议设置为租户内存的3-5%
- OLTP场景建议设置较大值（5%）
- OLAP场景可以适当降低（2-3%）

**2. 清理计划缓存**
```sql
-- 清理指定租户的计划缓存
ALTER SYSTEM FLUSH PLAN CACHE TENANT = tenant_name;

-- 清理全局计划缓存
ALTER SYSTEM FLUSH PLAN CACHE GLOBAL;
```

**3. 使用绑定变量**
```sql
-- 不好的做法（每次生成新的计划）
SELECT * FROM users WHERE id = 1;
SELECT * FROM users WHERE id = 2;
SELECT * FROM users WHERE id = 3;

-- 好的做法（使用绑定变量，复用计划）
PREPARE stmt FROM 'SELECT * FROM users WHERE id = ?';
EXECUTE stmt USING @id;
```

**4. 监控计划缓存淘汰**
```sql
-- 查看计划缓存淘汰情况
SELECT 
  tenant_id,
  svr_ip,
  evict_count AS eviction_count,
  ROUND((evict_count / NULLIF(hit_count + miss_count, 0)) * 100, 2) AS eviction_ratio
FROM oceanbase.GV$OB_PLAN_CACHE_STAT
WHERE tenant_id = 1001
ORDER BY evict_count DESC;
```

---

### 2. MemStore 使用率

#### 指标说明
MemStore是OceanBase的内存写缓冲区，所有写入操作首先进入MemStore。当MemStore达到阈值，会触发冻结（Freeze）操作，影响写入性能。

#### OceanBase存储机制

```
写入流程：
1. 数据写入 MemStore（内存）
2. MemStore达到阈值 → 触发冻结（Freeze）
3. 冻结的MemStore转储（Dump）到SSTable（磁盘）
4. Minor Compaction：合并增量SSTable
5. Major Compaction：全量合并，清理历史版本
```

#### 数据来源
```sql
-- 查看MemStore使用情况
SELECT 
  tenant_id,
  svr_ip,
  svr_port,
  active_memstore_used / 1024 / 1024 AS active_mb,
  freeze_trigger / 1024 / 1024 AS freeze_trigger_mb,
  ROUND(
    (active_memstore_used::DECIMAL / NULLIF(freeze_trigger, 0)) * 100,
    2
  ) AS usage_ratio,
  memstore_limit / 1024 / 1024 / 1024 AS memstore_limit_gb
FROM oceanbase.GV$OB_MEMSTORE
WHERE tenant_id = 1001
ORDER BY usage_ratio DESC;

-- 查看冻结历史
SELECT 
  tenant_id,
  freeze_type,  -- MINI/MINOR/MAJOR
  start_time,
  end_time,
  TIMESTAMPDIFF(SECOND, start_time, end_time) AS duration_seconds,
  status
FROM oceanbase.CDB_OB_FREEZE_INFO
WHERE tenant_id = 1001
ORDER BY start_time DESC
LIMIT 20;
```

#### 健康阈值
| MemStore使用率 | 状态 | 说明 | 健康度影响 |
|----------------|------|------|------------|
| < 60% | 🟢 健康 | 正常范围 | 无影响 |
| 60-70% | 🟡 正常 | 可接受 | -3分 |
| 70-80% | 🟠 关注 | 需要关注 | -7分 |
| 80-90% | 🔴 警告 | 可能触发冻结 | -12分 |
| > 90% | 🔴 严重 | 频繁冻结，影响性能 | -20分 |

#### 优化建议

**1. 调整MemStore配置**
```sql
-- 查看当前配置
SHOW PARAMETERS LIKE 'memstore%';

-- 调整MemStore大小（占租户内存的比例）
ALTER SYSTEM SET memstore_limit_percentage = 60 TENANT = tenant_name;

-- 调整冻结触发阈值
ALTER SYSTEM SET freeze_trigger_percentage = 70 TENANT = tenant_name;

-- 调整租户内存大小
ALTER RESOURCE UNIT unit_name MEMORY_SIZE = '20G';
```

**配置计算公式**：
```
MemStore大小 = 租户内存 × memstore_limit_percentage
冻结阈值 = MemStore大小 × freeze_trigger_percentage

示例：
租户内存 = 20G
memstore_limit_percentage = 60% → MemStore = 12G
freeze_trigger_percentage = 70% → 冻结阈值 = 8.4G
```

**2. 加速转储**
```sql
-- 查看转储进度
SELECT 
  tenant_id,
  svr_ip,
  tablet_id,
  status,  -- PENDING/RUNNING/FINISH
  start_time,
  now() - start_time AS duration
FROM oceanbase.GV$OB_TABLET_COMPACTION_PROGRESS
WHERE type = 'MINI_MERGE'
  AND status != 'FINISH'
ORDER BY start_time;

-- 调整转储并发度
ALTER SYSTEM SET minor_merge_concurrency = 4 TENANT = tenant_name;
```

**3. 监控写入压力**
```sql
-- 查看租户写入TPS
SELECT 
  tenant_id,
  COUNT(*) AS active_transactions,
  SUM(CASE WHEN state = 'ACTIVE' THEN 1 ELSE 0 END) AS active_count
FROM oceanbase.GV$OB_TRANSACTION_PARTICIPANTS
WHERE tenant_id = 1001
GROUP BY tenant_id;
```

---

### 3. RPC 性能指标

#### 指标说明
RPC (Remote Procedure Call) 是OceanBase分布式架构中节点间通信的核心机制。RPC性能直接影响分布式查询和事务的执行效率。

#### 数据来源
```sql
-- 查看RPC队列状态
SELECT 
  tenant_id,
  svr_ip,
  svr_port,
  pcode,  -- RPC类型代码
  queue_len AS rpc_queue_length,
  delay_us / 1000 AS delay_ms,
  req_cnt AS request_count
FROM oceanbase.GV$OB_RPC_OUTGOING
WHERE tenant_id = 1001
  AND queue_len > 0
ORDER BY queue_len DESC, delay_us DESC;

-- 查看RPC统计信息
SELECT 
  pcode,
  COUNT(*) AS rpc_count,
  AVG(delay_us / 1000) AS avg_delay_ms,
  MAX(delay_us / 1000) AS max_delay_ms,
  SUM(queue_len) AS total_queue_len
FROM oceanbase.GV$OB_RPC_OUTGOING
WHERE tenant_id = 1001
GROUP BY pcode
ORDER BY total_queue_len DESC
LIMIT 20;
```

#### 常见RPC类型（pcode）
| pcode | 说明 |
|-------|------|
| OB_TABLE_API_EXECUTE | 表操作执行 |
| OB_TRX_COMMIT | 事务提交 |
| OB_TRX_ROLLBACK | 事务回滚 |
| OB_SQL_SCAN | SQL扫描 |

#### 健康阈值
| RPC队列长度 | 状态 | 说明 | 健康度影响 |
|-------------|------|------|------------|
| 0-5 | 🟢 优秀 | 处理及时 | 无影响 |
| 6-10 | 🟡 良好 | 轻微积压 | -5分 |
| 11-50 | 🟠 警告 | 需要关注 | -10分 |
| > 50 | 🔴 严重 | 严重积压，可能超时 | -20分 |

#### 优化建议

**1. 诊断RPC积压原因**
```sql
-- 查找慢RPC请求
SELECT 
  tenant_id,
  svr_ip,
  pcode,
  queue_len,
  delay_us / 1000 AS delay_ms,
  req_cnt
FROM oceanbase.GV$OB_RPC_OUTGOING
WHERE delay_us > 100000  -- >100ms
ORDER BY delay_us DESC;

-- 检查相关SQL
SELECT 
  tenant_id,
  svr_ip,
  sql_id,
  LEFT(query_sql, 100) AS sql_preview,
  elapsed_time / 1000 AS elapsed_ms,
  execute_time / 1000 AS execute_ms
FROM oceanbase.GV$OB_SQL_AUDIT
WHERE tenant_id = 1001
  AND elapsed_time > 100000
ORDER BY elapsed_time DESC
LIMIT 20;
```

**2. 调整RPC超时配置**
```sql
-- 查看RPC超时配置
SHOW PARAMETERS LIKE '%rpc_timeout%';

-- 调整RPC超时时间（微秒）
ALTER SYSTEM SET rpc_timeout = 3000000 TENANT = tenant_name;  -- 3秒
```

**3. 网络优化**
```sql
-- 检查网络延迟
SELECT 
  svr_ip,
  svr_port,
  AVG(net_time_us / 1000) AS avg_network_ms
FROM oceanbase.GV$OB_SQL_AUDIT
WHERE tenant_id = 1001
  AND net_time_us > 0
GROUP BY svr_ip, svr_port
ORDER BY avg_network_ms DESC;
```

---

### 4. 合并（Compaction）指标

#### 指标说明
OceanBase通过合并机制管理数据版本和存储空间。合并分为Minor Compaction（增量合并）和Major Compaction（全量合并）。

#### Minor Compaction（增量合并）

**数据来源**：
```sql
-- 查看Minor合并进度
SELECT 
  tenant_id,
  tablet_id,
  svr_ip,
  status,
  data_size / 1024 / 1024 AS data_size_mb,
  start_time,
  TIMESTAMPDIFF(SECOND, start_time, now()) AS duration_seconds
FROM oceanbase.GV$OB_TABLET_COMPACTION_PROGRESS
WHERE type = 'MINOR_MERGE'
  AND tenant_id = 1001
ORDER BY start_time DESC
LIMIT 20;

-- 统计待处理的Minor合并任务
SELECT 
  tenant_id,
  COUNT(*) AS pending_minor_compactions,
  SUM(data_size) / 1024 / 1024 / 1024 AS total_data_gb
FROM oceanbase.GV$OB_TABLET_COMPACTION_PROGRESS
WHERE type = 'MINOR_MERGE'
  AND status != 'FINISH'
  AND tenant_id = 1001
GROUP BY tenant_id;
```

**健康阈值**：
| 待处理Minor合并数 | 状态 | 说明 |
|-------------------|------|------|
| < 20 | 🟢 正常 | 合并及时 |
| 20-50 | 🟡 关注 | 轻微积压 |
| 50-100 | 🟠 警告 | 需要优化 |
| > 100 | 🔴 严重 | 严重积压 |

#### Major Compaction（全量合并）

**数据来源**：
```sql
-- 查看Major合并状态
SELECT 
  zone,
  broadcast_scn,
  last_scn,
  is_merge_error,
  is_suspended,
  info
FROM oceanbase.CDB_OB_MAJOR_COMPACTION
WHERE tenant_id = 1001;

-- 查看Major合并进度
SELECT 
  tenant_id,
  svr_ip,
  tablet_id,
  status,
  data_size / 1024 / 1024 / 1024 AS data_size_gb,
  progressive_compaction_round,
  start_time,
  TIMESTAMPDIFF(SECOND, start_time, now()) AS duration_seconds
FROM oceanbase.GV$OB_TABLET_COMPACTION_PROGRESS
WHERE type = 'MAJOR_MERGE'
  AND tenant_id = 1001
ORDER BY start_time DESC
LIMIT 20;

-- 查看Major合并历史
SELECT 
  tenant_id,
  start_time,
  finish_time,
  TIMESTAMPDIFF(SECOND, start_time, finish_time) AS duration_seconds,
  is_error,
  error_msg
FROM oceanbase.CDB_OB_MAJOR_COMPACTION_HISTORY
WHERE tenant_id = 1001
ORDER BY start_time DESC
LIMIT 10;
```

**健康阈值**：
| 合并状态 | 健康度影响 |
|----------|------------|
| 已完成（100%） | 无影响 |
| 进行中（< 2小时） | -3分 |
| 进行中（2-6小时） | -8分 |
| 进行中（> 6小时） | -15分 |
| 失败 | -25分 |

#### 优化建议

**1. 配置合并时间窗口**
```sql
-- 查看合并配置
SHOW PARAMETERS LIKE '%major_freeze%';

-- 设置Major合并时间窗口（业务低峰期）
ALTER SYSTEM SET major_freeze_duty_time = '02:00' TENANT = tenant_name;

-- 设置合并并发度
ALTER SYSTEM SET minor_merge_concurrency = 4 TENANT = tenant_name;
ALTER SYSTEM SET ha_mid_thread_score = 100;  -- 调整合并线程优先级
```

**2. 手动触发合并**
```sql
-- 手动触发Major合并（业务低峰期）
ALTER SYSTEM MAJOR FREEZE TENANT = tenant_name;

-- 查看合并触发历史
SELECT 
  freeze_version,
  freeze_type,
  frozen_scn,
  frozen_time
FROM oceanbase.CDB_OB_FREEZE_INFO
WHERE tenant_id = 1001
ORDER BY frozen_time DESC
LIMIT 10;
```

**3. 监控合并性能**
```sql
-- 查看合并IO统计
SELECT 
  tenant_id,
  svr_ip,
  SUM(write_bytes) / 1024 / 1024 AS total_write_mb,
  SUM(read_bytes) / 1024 / 1024 AS total_read_mb
FROM oceanbase.GV$OB_COMPACTION_DIAGNOSE_INFO
WHERE tenant_id = 1001
GROUP BY tenant_id, svr_ip;
```

**最佳实践**：
- Major Compaction应在业务低峰期执行（凌晨2-6点）
- 确保合并在业务高峰前完成
- 监控合并进度，避免长时间未完成
- 合并期间可能影响查询性能，需要预留资源

---

### 5. Tablet 管理

#### 指标说明
Tablet是OceanBase数据分片的基本单位，类似于分区的概念。Tablet的分布和数量直接影响系统性能和扩展性。

#### 数据来源
```sql
-- 查看Tablet分布
SELECT 
  tenant_id,
  table_id,
  tablet_id,
  svr_ip,
  role,  -- LEADER/FOLLOWER
  replica_type,  -- FULL/LOGONLY
  data_size / 1024 / 1024 AS data_size_mb
FROM oceanbase.CDB_OB_TABLE_LOCATIONS
WHERE tenant_id = 1001
ORDER BY data_size DESC
LIMIT 50;

-- 统计Tablet数量
SELECT 
  tenant_id,
  COUNT(DISTINCT tablet_id) AS tablet_count,
  COUNT(DISTINCT CASE WHEN role = 'LEADER' THEN tablet_id END) AS leader_count,
  SUM(data_size) / 1024 / 1024 / 1024 AS total_data_gb
FROM oceanbase.CDB_OB_TABLE_LOCATIONS
WHERE tenant_id = 1001
GROUP BY tenant_id;

-- 查看Leader分布是否均衡
SELECT 
  svr_ip,
  COUNT(CASE WHEN role = 'LEADER' THEN 1 END) AS leader_count,
  COUNT(*) AS total_replicas
FROM oceanbase.CDB_OB_TABLE_LOCATIONS
WHERE tenant_id = 1001
GROUP BY svr_ip
ORDER BY leader_count DESC;
```

#### 健康阈值
| Tablet数量 | 状态 | 说明 |
|-----------|------|------|
| < 10万 | 🟢 正常 | 管理简单 |
| 10-50万 | 🟡 关注 | 需要关注性能 |
| 50-100万 | 🟠 警告 | 可能影响性能 |
| > 100万 | 🔴 严重 | 需要优化分区策略 |

#### 优化建议

**1. 优化分区策略**
```sql
-- 查看表分区信息
SELECT 
  table_name,
  partition_name,
  high_value,
  table_rows,
  data_length / 1024 / 1024 AS data_mb
FROM information_schema.PARTITIONS
WHERE table_schema = 'your_database'
  AND table_name = 'your_table'
ORDER BY partition_ordinal_position;

-- 合并小分区
ALTER TABLE table_name REORGANIZE PARTITION p1, p2 INTO (PARTITION p_new ...);

-- 拆分大分区
ALTER TABLE table_name SPLIT PARTITION p1 INTO (
  PARTITION p1_1 VALUES LESS THAN (...),
  PARTITION p1_2 VALUES LESS THAN (...)
);
```

**2. Leader分布均衡**
```sql
-- 查看Leader分布不均的情况
SELECT 
  a.svr_ip,
  a.leader_count,
  ROUND(a.leader_count * 100.0 / b.total_leaders, 2) AS leader_percentage
FROM (
  SELECT svr_ip, COUNT(*) AS leader_count
  FROM oceanbase.CDB_OB_TABLE_LOCATIONS
  WHERE role = 'LEADER' AND tenant_id = 1001
  GROUP BY svr_ip
) a
CROSS JOIN (
  SELECT COUNT(*) AS total_leaders
  FROM oceanbase.CDB_OB_TABLE_LOCATIONS
  WHERE role = 'LEADER' AND tenant_id = 1001
) b
ORDER BY leader_percentage DESC;

-- 手动触发Leader切换（谨慎使用）
ALTER SYSTEM SWITCH REPLICA LEADER ls_id = xxx SERVER = 'ip:port';
```

---

### 6. SQL执行分析

#### SQL审计（SQL Audit）

**数据来源**：
```sql
-- 查看慢SQL（Top 20）
SELECT 
  tenant_id,
  sql_id,
  user_name,
  db_name,
  LEFT(query_sql, 100) AS sql_preview,
  elapsed_time / 1000 AS elapsed_ms,
  execute_time / 1000 AS execute_ms,
  queue_time / 1000 AS queue_ms,
  get_plan_time / 1000 AS get_plan_ms,
  affected_rows,
  return_rows,
  request_time
FROM oceanbase.GV$OB_SQL_AUDIT
WHERE tenant_id = 1001
  AND elapsed_time > 100000  -- >100ms
ORDER BY elapsed_time DESC
LIMIT 20;

-- 统计SQL执行情况
SELECT 
  DATE_FORMAT(request_time, '%Y-%m-%d %H:00:00') AS hour,
  COUNT(*) AS sql_count,
  AVG(elapsed_time / 1000) AS avg_elapsed_ms,
  MAX(elapsed_time / 1000) AS max_elapsed_ms,
  SUM(CASE WHEN elapsed_time > 1000000 THEN 1 ELSE 0 END) AS slow_sql_count
FROM oceanbase.GV$OB_SQL_AUDIT
WHERE tenant_id = 1001
  AND request_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY hour
ORDER BY hour DESC;
```

#### 执行计划分析

**获取执行计划**：
```sql
-- 查看SQL执行计划
EXPLAIN SELECT * FROM users WHERE id = 1;

-- 详细执行计划
EXPLAIN EXTENDED SELECT * FROM users WHERE id = 1;

-- 查看实际执行计划（包含真实行数）
EXPLAIN PLAN_CACHE SELECT * FROM users WHERE id = 1;

-- 查看分布式执行计划
EXPLAIN DISTRIBUTED SELECT * FROM users WHERE id = 1;
```

**关键指标**：
- **执行方式**: LOCAL/REMOTE/DISTRIBUTED
- **访问方式**: TABLE_SCAN/INDEX_SCAN/INDEX_LOOKUP
- **分区裁剪**: 是否有效利用分区
- **并行度**: 是否使用并行执行

#### 优化建议

**1. SQL性能分析**
```sql
-- 查看SQL统计信息
SELECT 
  sql_id,
  plan_id,
  COUNT(*) AS exec_count,
  AVG(elapsed_time / 1000) AS avg_elapsed_ms,
  AVG(execute_time / 1000) AS avg_execute_ms,
  AVG(get_plan_time / 1000) AS avg_plan_time_ms,
  AVG(return_rows) AS avg_return_rows,
  AVG(affected_rows) AS avg_affected_rows
FROM oceanbase.GV$OB_SQL_AUDIT
WHERE tenant_id = 1001
  AND request_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY sql_id, plan_id
ORDER BY AVG(elapsed_time) DESC
LIMIT 20;
```

**2. 索引优化**
```sql
-- 查看表索引使用情况
SELECT 
  table_schema,
  table_name,
  index_name,
  cardinality,
  index_type
FROM information_schema.STATISTICS
WHERE table_schema = 'your_database'
ORDER BY table_name, index_name;

-- 创建索引
CREATE INDEX idx_column ON table_name (column) LOCAL;

-- 删除未使用的索引
DROP INDEX idx_name ON table_name;
```

---

## 分布式特性监控

### 1. 副本同步状态

#### 数据来源
```sql
-- 查看副本状态
SELECT 
  tenant_id,
  ls_id,  -- Log Stream ID
  svr_ip,
  role,
  proposal_id,
  data_size / 1024 / 1024 AS data_size_mb,
  required_size / 1024 / 1024 AS required_size_mb
FROM oceanbase.CDB_OB_LS_LOCATIONS
WHERE tenant_id = 1001
ORDER BY ls_id, role;

-- 检查副本一致性
SELECT 
  ls_id,
  COUNT(DISTINCT role) AS role_count,
  COUNT(*) AS replica_count,
  MAX(data_size) - MIN(data_size) AS size_diff
FROM oceanbase.CDB_OB_LS_LOCATIONS
WHERE tenant_id = 1001
GROUP BY ls_id
HAVING COUNT(DISTINCT role) < 2  -- 缺少Leader或Follower
   OR COUNT(*) < 3;  -- 副本数不足
```

### 2. Paxos日志同步

```sql
-- 查看日志同步延迟
SELECT 
  tenant_id,
  ls_id,
  svr_ip,
  role,
  proposal_id,
  begin_lsn,
  end_lsn
FROM oceanbase.GV$OB_LOG_STAT
WHERE tenant_id = 1001
ORDER BY ls_id;
```

---

## OceanBase 配置优化

### 租户资源配置

```sql
-- 查看租户资源配置
SELECT 
  tenant_name,
  unit_config_name,
  max_cpu,
  min_cpu,
  memory_size / 1024 / 1024 / 1024 AS memory_gb,
  log_disk_size / 1024 / 1024 / 1024 AS log_disk_gb
FROM oceanbase.DBA_OB_TENANTS t
JOIN oceanbase.DBA_OB_RESOURCE_POOLS p ON t.tenant_id = p.tenant_id
JOIN oceanbase.DBA_OB_UNIT_CONFIGS c ON p.unit_config_id = c.unit_config_id
WHERE t.tenant_name = 'your_tenant';

-- 创建资源单元
CREATE RESOURCE UNIT unit_name 
  MAX_CPU = 4, 
  MIN_CPU = 2, 
  MEMORY_SIZE = '20G', 
  LOG_DISK_SIZE = '50G';

-- 修改租户资源
ALTER RESOURCE TENANT tenant_name UNIT = 'unit_name';
```

### 系统参数优化

```sql
-- 查看所有参数
SHOW PARAMETERS;

-- 查看特定参数
SHOW PARAMETERS LIKE '%cache%';

-- 租户级别设置
ALTER SYSTEM SET parameter_name = 'value' TENANT = tenant_name;

-- 集群级别设置
ALTER SYSTEM SET parameter_name = 'value';

-- Server级别设置
ALTER SYSTEM SET parameter_name = 'value' SERVER = 'ip:port';
```

### 推荐配置模板

```sql
-- ========== 内存相关 ==========
-- 租户内存：20G
-- MemStore：12G（60%）
ALTER SYSTEM SET memstore_limit_percentage = 60 TENANT = tenant_name;
ALTER SYSTEM SET freeze_trigger_percentage = 70 TENANT = tenant_name;

-- 计划缓存：1G（5%）
ALTER SYSTEM SET plan_cache_mem_limit = '1G' TENANT = tenant_name;

-- ========== 合并相关 ==========
-- Major合并时间窗口
ALTER SYSTEM SET major_freeze_duty_time = '02:00' TENANT = tenant_name;

-- 合并并发度
ALTER SYSTEM SET minor_merge_concurrency = 4 TENANT = tenant_name;

-- ========== 性能相关 ==========
-- RPC超时
ALTER SYSTEM SET rpc_timeout = 3000000 TENANT = tenant_name;  -- 3秒

-- 查询超时
ALTER SYSTEM SET ob_query_timeout = 10000000 TENANT = tenant_name;  -- 10秒

-- 事务超时
ALTER SYSTEM SET ob_trx_timeout = 100000000 TENANT = tenant_name;  -- 100秒

-- ========== 日志相关 ==========
-- 启用SQL审计
ALTER SYSTEM SET enable_sql_audit = true TENANT = tenant_name;

-- 慢查询阈值
ALTER SYSTEM SET trace_log_slow_query_watermark = 100000 TENANT = tenant_name;  -- 100ms
```

---

## 性能问题排查

### 常见问题诊断流程

**1. CPU高**
```sql
-- 查找CPU密集SQL
SELECT 
  sql_id,
  LEFT(query_sql, 100) AS sql_preview,
  COUNT(*) AS exec_count,
  AVG(elapsed_time / 1000) AS avg_elapsed_ms,
  SUM(elapsed_time / 1000) AS total_elapsed_ms
FROM oceanbase.GV$OB_SQL_AUDIT
WHERE tenant_id = 1001
  AND request_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY sql_id
ORDER BY total_elapsed_ms DESC
LIMIT 20;
```

**2. 内存压力**
```sql
-- 检查MemStore使用
-- （参考前文MemStore章节）

-- 检查租户内存使用
SELECT 
  tenant_id,
  tenant_name,
  mem_limit / 1024 / 1024 / 1024 AS mem_limit_gb,
  mem_used / 1024 / 1024 / 1024 AS mem_used_gb,
  ROUND((mem_used * 100.0 / mem_limit), 2) AS usage_ratio
FROM oceanbase.GV$OB_TENANT
WHERE tenant_id = 1001;
```

**3. 写入性能下降**
```sql
-- 检查MemStore冻结频率
SELECT 
  DATE_FORMAT(start_time, '%Y-%m-%d %H:%i') AS time_window,
  COUNT(*) AS freeze_count,
  AVG(TIMESTAMPDIFF(SECOND, start_time, end_time)) AS avg_duration_sec
FROM oceanbase.CDB_OB_FREEZE_INFO
WHERE tenant_id = 1001
  AND freeze_type = 'MINI'
  AND start_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY time_window
ORDER BY time_window DESC;
```

**4. 查询性能下降**
```sql
-- 检查计划缓存命中率
-- （参考前文计划缓存章节）

-- 检查是否有表扫描
SELECT 
  sql_id,
  LEFT(query_sql, 100) AS sql_preview,
  COUNT(*) AS exec_count,
  AVG(affected_rows) AS avg_affected_rows
FROM oceanbase.GV$OB_SQL_AUDIT
WHERE tenant_id = 1001
  AND query_sql LIKE '%TABLE%SCAN%'
  AND request_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY sql_id
ORDER BY exec_count DESC
LIMIT 20;
```

---

## 监控告警阈值

| 告警级别 | 指标 | 阈值 | 处理时效 |
|----------|------|------|----------|
| 🔴 P1严重 | 计划缓存命中率 | < 85% | 立即处理 |
| 🔴 P1严重 | MemStore使用率 | > 90% | 立即处理 |
| 🔴 P1严重 | RPC队列长度 | > 100 | 立即处理 |
| 🔴 P1严重 | Major合并失败 | 失败 | 立即处理 |
| 🟠 P2重要 | MemStore使用率 | > 80% | 1小时内 |
| 🟠 P2重要 | RPC队列长度 | > 50 | 1小时内 |
| 🟠 P2重要 | Minor合并积压 | > 100 | 1小时内 |
| 🟠 P2重要 | Major合并超时 | > 6小时 | 1小时内 |
| 🟡 P3一般 | 计划缓存命中率 | < 95% | 24小时内 |
| 🟡 P3一般 | Tablet数量 | > 50万 | 24小时内 |

---

## OceanBase vs MySQL vs PostgreSQL

### 架构差异对比

| 特性 | OceanBase | MySQL | PostgreSQL |
|------|-----------|-------|------------|
| 架构 | 原生分布式 | 单机（需中间件分布式） | 单机（需插件分布式） |
| 存储 | LSM-Tree | B+Tree | B+Tree |
| 并发控制 | MVCC + Paxos | MVCC | MVCC |
| 数据一致性 | 强一致（Paxos） | 最终一致（异步复制） | 最终一致（异步复制） |
| 扩展性 | 水平扩展 | 垂直扩展为主 | 垂直扩展为主 |

### 关键指标对比

| 指标 | OceanBase | MySQL | PostgreSQL |
|------|-----------|-------|------------|
| 最关键指标 | 计划缓存命中率 | Buffer Pool命中率 | 缓冲区命中率 |
| 特有问题 | MemStore冻结 | 死锁 | 表膨胀 |
| 维护重点 | 合并策略 | 索引维护 | VACUUM策略 |
| 扩展方式 | 增加节点 | 读写分离/分库分表 | 连接池/分区表 |

---

## 总结

OceanBase性能优化关键点：

1. **计划缓存命中率**：保持≥98%，这是最重要的性能指标
2. **MemStore管理**：避免频繁冻结，保持使用率<80%
3. **RPC性能**：监控队列长度，优化分布式查询
4. **合并策略**：合理安排Major Compaction时间窗口
5. **租户资源**：合理规划租户内存和CPU配额
6. **Tablet管理**：优化分区策略，避免Tablet数量过多

**记住**：OceanBase是分布式数据库，需要特别关注分布式特性带来的性能影响！

**最佳实践**：
- 使用绑定变量提高计划缓存命中率
- 业务低峰期执行Major Compaction
- 定期检查Leader分布是否均衡
- 监控MemStore使用率，避免频繁冻结
- 合理设计分区策略，控制Tablet数量
