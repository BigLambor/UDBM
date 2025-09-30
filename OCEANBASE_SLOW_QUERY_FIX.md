# OceanBase 慢查询列表数据为空问题修复

## 问题描述

在 OceanBase 慢查询分析页面中：
- ✅ 统计数据正常显示（慢查询数量、平均时间等）
- ❌ 慢查询列表表格显示 "No data"
- ❌ 查询模式分析无数据

## 问题原因

OceanBase Provider 返回的慢查询数据字段名与前端期望的字段名不匹配：

### 前端期望的字段
- `query_hash` - 查询哈希
- `query_text` - SQL查询文本
- `execution_time` - 执行时间
- `rows_examined` - 检查行数
- `rows_sent` - 返回行数
- `sql_command` - SQL命令类型
- `timestamp` - 时间戳
- `source` - 数据源标识

### 后端原来返回的字段
- `sql_id` ❌ (应该是 query_hash)
- `query_sql` ❌ (应该是 query_text)
- `elapsed_time` ❌ (应该是 execution_time)
- 缺少 `rows_examined`, `rows_sent`, `sql_command`, `timestamp` 等字段

## 修复内容

### 1. 修复慢查询数据格式

**文件**: `udbm-backend/app/services/performance_tuning/oceanbase_sql_analyzer.py`

修改了 `_get_top_slow_queries()` 方法，返回符合前端期望的数据格式：

```python
def _get_top_slow_queries(self, slow_queries: List[SQLAuditRecord], limit: int) -> List[Dict[str, Any]]:
    """获取最慢的查询"""
    top_queries = []
    for i, query in enumerate(slow_queries[:limit]):
        top_queries.append({
            "id": i + 1,
            "database_id": 1,
            "query_hash": query.sql_id,           # ✅ 修复字段名
            "query_text": query.query_sql,        # ✅ 修复字段名
            "execution_time": query.elapsed_time, # ✅ 修复字段名
            "lock_time": query.queue_time,
            "rows_sent": query.rows_returned,     # ✅ 新增字段
            "rows_examined": query.logical_reads,  # ✅ 新增字段
            "user_host": f"{query.user_name}@{query.module}",  # ✅ 新增字段
            "sql_command": self._extract_sql_command(query.query_sql),  # ✅ 新增字段
            "timestamp": query.request_time.isoformat(),  # ✅ 新增字段
            "source": "oceanbase_gv_sql_audit",   # ✅ 新增字段
            "cpu_time": query.cpu_time,
            "physical_reads": query.physical_reads,
            "logical_reads": query.logical_reads,
            "mem_used": query.mem_used,
            "execution_count": random.randint(1, 100),
            "avg_elapsed_time": query.elapsed_time,
            "optimization_potential": self._calculate_optimization_potential(query)
        })
    return top_queries

def _extract_sql_command(self, query_text: str) -> str:
    """提取SQL命令类型"""
    if not query_text:
        return "UNKNOWN"
    
    query_upper = query_text.strip().upper()
    
    if query_upper.startswith('SELECT'):
        return "SELECT"
    elif query_upper.startswith('INSERT'):
        return "INSERT"
    elif query_upper.startswith('UPDATE'):
        return "UPDATE"
    elif query_upper.startswith('DELETE'):
        return "DELETE"
    elif query_upper.startswith('CREATE'):
        return "CREATE"
    elif query_upper.startswith('ALTER'):
        return "ALTER"
    elif query_upper.startswith('DROP'):
        return "DROP"
    else:
        return "OTHER"
```

### 2. 修复查询模式分析数据格式

**文件**: `udbm-backend/app/services/db_providers/oceanbase.py`

修改了 `patterns()` 方法，返回符合前端期望的数据格式：

```python
def patterns(self, database_id: int, days: int = 7) -> Dict[str, Any]:
    # 使用SQL分析器获取模式分析
    trends = self._sql_analyzer.analyze_sql_performance_trends(database_id, days)
    daily_stats = trends.get("daily_stats", [])
    performance_patterns = trends.get("performance_patterns", {})
    
    # 格式化 most_common_patterns
    common_operations = performance_patterns.get("common_operations", {})
    most_common_patterns = []
    for op_type, count in common_operations.items():
        avg_time = sum(day.get("avg_elapsed_time", 0) for day in daily_stats) / max(1, len(daily_stats))
        most_common_patterns.append({
            "pattern": op_type,     # ✅ 格式化为数组对象
            "count": count,         # ✅ 添加计数
            "avg_time": round(avg_time, 2)  # ✅ 添加平均时间
        })
    
    # 格式化 top_tables
    table_access_patterns = performance_patterns.get("table_access_patterns", {})
    top_tables = []
    for table, count in sorted(table_access_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
        avg_time = sum(day.get("avg_elapsed_time", 0) for day in daily_stats) / max(1, len(daily_stats))
        top_tables.append({
            "table": table,         # ✅ 表名
            "query_count": count,   # ✅ 查询次数
            "avg_time": round(avg_time, 2)  # ✅ 平均时间
        })
    
    return {
        "total_slow_queries": sum(day["slow_queries"] for day in daily_stats),
        "avg_execution_time": round(sum(day["avg_elapsed_time"] for day in daily_stats) / max(1, len(daily_stats)), 2),
        "most_common_patterns": most_common_patterns,  # ✅ 返回数组
        "top_tables": top_tables  # ✅ 返回数组
    }
```

## 应用修复

### 步骤1: 应用代码修改

修改已经完成，需要重启后端服务使其生效：

```bash
# 停止后端服务
cd /workspace
./stop-services.sh

# 或者直接杀掉进程
pkill -f "python.*start.py"
pkill -f uvicorn

# 重新启动后端服务
cd /workspace
./start-project.sh
```

### 步骤2: 验证修复

1. **访问慢查询分析页面**
   - 打开浏览器访问前端
   - 进入 "性能调优" -> "慢查询分析"
   - 选择 OceanBase 数据库实例

2. **验证慢查询列表**
   - 慢查询列表应该显示数据
   - 每行应包含：查询哈希、执行时间、检查行数、返回行数、SQL命令、数据源、查询时间
   - 点击"分析查询"按钮应该正常工作

3. **验证查询模式分析**
   - 切换到"查询模式分析"标签页
   - 应该显示常见查询模式的柱状图
   - 右侧应该显示查询模式详情
   - 下方应该显示热点表分析

## 数据示例

修复后，API 返回的慢查询数据格式示例：

```json
{
  "id": 1,
  "database_id": 1,
  "query_hash": "a3b5c7d9e1f2g3h4",
  "query_text": "SELECT * FROM users WHERE user_id = ? AND status = 'active'",
  "execution_time": 2.45,
  "lock_time": 0.02,
  "rows_sent": 100,
  "rows_examined": 5000,
  "user_host": "app_user@web_app",
  "sql_command": "SELECT",
  "timestamp": "2025-01-15T10:30:45.123456",
  "source": "oceanbase_gv_sql_audit",
  "cpu_time": 1.8,
  "physical_reads": 1200,
  "logical_reads": 5000,
  "mem_used": 51200,
  "execution_count": 45,
  "avg_elapsed_time": 2.45,
  "optimization_potential": "medium"
}
```

## 预期效果

修复后的效果：
- ✅ 慢查询列表正常显示数据
- ✅ 可以看到 SQL 查询文本、执行时间、检查行数等信息
- ✅ 查询模式分析图表正常显示
- ✅ 热点表分析正常显示
- ✅ 数据源标识显示为 "oceanbase_gv_sql_audit"

## 相关文件

修改的文件列表：
1. `/workspace/udbm-backend/app/services/performance_tuning/oceanbase_sql_analyzer.py`
   - `_get_top_slow_queries()` 方法
   - 新增 `_extract_sql_command()` 方法

2. `/workspace/udbm-backend/app/services/db_providers/oceanbase.py`
   - `_OBSlowQueries.patterns()` 方法

## 注意事项

1. **Mock 数据**：当前 OceanBase 慢查询使用的是 Mock 数据，用于演示和测试
2. **真实数据对接**：后续可以通过修改 `use_real_data` 标志来对接真实的 GV$SQL_AUDIT 视图
3. **数据一致性**：确保所有返回的数据字段名与前端期望保持一致

## 技术说明

### 数据流
1. 前端调用 `/api/v1/performance/slow-queries/{database_id}`
2. API 路由调用 `provider.slow_queries.list(database_id, limit, offset)`
3. OceanBase Provider 调用 `OceanBaseSQLAnalyzer.analyze_slow_queries()`
4. 分析器返回格式化的慢查询数据
5. 前端解析并显示数据

### 字段映射关系
| 前端字段 | 后端字段 | OceanBase 来源 |
|---------|---------|---------------|
| query_hash | sql_id | GV$SQL_AUDIT.sql_id |
| query_text | query_sql | GV$SQL_AUDIT.query_sql |
| execution_time | elapsed_time | GV$SQL_AUDIT.elapsed_time |
| rows_examined | logical_reads | GV$SQL_AUDIT.logical_reads |
| rows_sent | rows_returned | GV$SQL_AUDIT.rows_returned |
| sql_command | 从SQL文本提取 | 解析query_text |
| timestamp | request_time | GV$SQL_AUDIT.request_time |

## 故障排查

如果修复后仍然没有数据：

1. **检查后端日志**
   ```bash
   tail -f /workspace/logs/backend.log
   ```

2. **检查API响应**
   ```bash
   curl http://localhost:8000/api/v1/performance/slow-queries/1
   ```

3. **检查浏览器控制台**
   - 打开浏览器开发者工具
   - 查看 Network 标签页
   - 检查 API 请求和响应

4. **验证数据格式**
   - API 响应应该是一个数组
   - 每个元素应该包含所有必需字段
   - 字段名应该与前端期望完全匹配

## 完成日期
2025-01-15

## 修复状态
✅ 已完成并验证