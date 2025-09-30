# OceanBase 真实环境配置指南

## 概述

本项目现在支持使用真正的OceanBase社区版Docker镜像，而不是MySQL模拟。这样可以获得更真实的OceanBase特性和性能表现。

## 系统要求

- Docker Desktop 4.0+
- 至少4GB可用内存
- 至少10GB可用磁盘空间

## 快速开始

### 1. 使用真正的OceanBase启动

```bash
# 启动真正的OceanBase环境
./start-oceanbase.sh
```

### 2. 验证连接

```bash
# 测试OceanBase连接
python test_oceanbase_real.py
```

### 3. 手动连接

```bash
# 使用MySQL客户端连接
mysql -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password

# 或使用Docker内的obclient
docker exec -it udbm-oceanbase obclient -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password
```

## 配置详情

### Docker Compose配置

```yaml
oceanbase:
  image: oceanbase/oceanbase-ce:latest
  container_name: udbm-oceanbase
  environment:
    - OB_ROOT_PASSWORD=udbm_ob_root_password
    - OB_CLUSTER_NAME=obcluster
    - OB_TENANT_NAME=test
  ports:
    - "2881:2881"  # OceanBase默认端口
    - "2882:2882"  # OceanBase RPC端口
  volumes:
    - oceanbase_data:/root/ob
  privileged: true
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G
```

### 连接参数

- **主机**: localhost
- **端口**: 2881
- **用户名**: root@test
- **密码**: udbm_ob_root_password
- **数据库**: udbm_oceanbase_demo

## OceanBase特有功能

### 1. 系统视图

OceanBase提供了丰富的系统视图来监控性能：

```sql
-- 查看集群信息
SELECT * FROM oceanbase.__all_server;

-- 查看租户信息
SELECT * FROM oceanbase.__all_tenant;

-- 查看资源使用情况
SELECT * FROM oceanbase.__all_virtual_memory_info;
```

### 2. 性能监控

```sql
-- 查看SQL执行统计
SELECT * FROM oceanbase.__all_virtual_sql_audit;

-- 查看慢查询
SELECT * FROM oceanbase.__all_virtual_sql_audit 
WHERE elapsed_time > 1000000;  -- 1秒

-- 查看计划缓存
SELECT * FROM oceanbase.__all_virtual_plan_cache_stat;
```

### 3. 分区管理

```sql
-- 查看分区表信息
SELECT * FROM information_schema.partitions 
WHERE table_schema = 'udbm_oceanbase_demo';

-- 查看分区热点
SELECT * FROM oceanbase.__all_virtual_partition_info;
```

## 与MySQL模拟的差异

| 特性 | MySQL模拟 | 真正的OceanBase |
|------|-----------|-----------------|
| 系统视图 | 有限 | 丰富 |
| 分区支持 | 基础 | 完整 |
| 多租户 | 无 | 原生支持 |
| 压缩 | 基础 | 高级 |
| 分布式 | 无 | 原生支持 |
| 监控指标 | 模拟 | 真实 |

## 故障排除

### 1. 内存不足

如果遇到内存不足错误：

```bash
# 检查Docker内存限制
docker stats udbm-oceanbase

# 增加内存限制
# 在docker-compose.yml中调整deploy.resources.limits.memory
```

### 2. 启动失败

```bash
# 查看容器日志
docker logs udbm-oceanbase

# 检查系统资源
docker system df
docker system prune
```

### 3. 连接失败

```bash
# 检查端口是否开放
netstat -tlnp | grep 2881

# 检查容器状态
docker ps | grep oceanbase
```

## 性能优化建议

### 1. 内存配置

```sql
-- 调整租户内存
ALTER RESOURCE POOL sys_pool MEMORY_LIMIT='2G';

-- 调整系统内存
ALTER SYSTEM SET memory_limit='4G';
```

### 2. 并发配置

```sql
-- 调整最大连接数
ALTER SYSTEM SET max_connections=1000;

-- 调整工作线程数
ALTER SYSTEM SET cpu_count=8;
```

### 3. 存储优化

```sql
-- 启用压缩
ALTER TABLE users COMPRESS='lz4_1.0';

-- 调整合并策略
ALTER SYSTEM SET major_freeze_duty_time='02:00:00';
```

## 监控和告警

### 1. 关键指标

- **CPU使用率**: 应保持在80%以下
- **内存使用率**: 应保持在85%以下
- **计划缓存命中率**: 应保持在90%以上
- **RPC队列长度**: 应保持在20以下

### 2. 告警规则

```sql
-- 创建告警规则示例
CREATE ALERT RULE high_cpu_usage
WHEN cpu_usage > 80
FOR 5m
DO ALERT 'CPU使用率过高';

CREATE ALERT RULE low_cache_hit
WHEN plan_cache_hit_ratio < 90
FOR 2m
DO ALERT '计划缓存命中率过低';
```

## 备份和恢复

### 1. 数据备份

```bash
# 使用mysqldump备份
mysqldump -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password udbm_oceanbase_demo > backup.sql

# 使用OceanBase工具备份
docker exec udbm-oceanbase obdumper -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password -D udbm_oceanbase_demo
```

### 2. 数据恢复

```bash
# 恢复数据
mysql -h127.0.0.1 -P2881 -uroot@test -pudbm_ob_root_password udbm_oceanbase_demo < backup.sql
```

## 开发建议

### 1. 使用OceanBase特有功能

- 利用多租户架构
- 使用分区表优化查询
- 利用压缩减少存储空间
- 使用OceanBase的监控视图

### 2. 性能测试

```bash
# 运行性能测试
python test_oceanbase_real.py

# 运行压力测试
python -m pytest tests/performance/ -v
```

### 3. 监控集成

将OceanBase的真实监控数据集成到UDBM平台中，提供更准确的性能分析和优化建议。

## 总结

使用真正的OceanBase可以获得：

1. **真实的性能数据** - 不再是模拟数据
2. **完整的特性支持** - 多租户、分区、压缩等
3. **准确的监控指标** - 基于真实系统状态
4. **更好的优化建议** - 基于OceanBase特有的优化策略

建议在生产环境或需要真实OceanBase特性的场景中使用此配置。
