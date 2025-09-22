"""
OceanBase SQL性能分析器
基于GV$SQL_AUDIT视图进行SQL性能分析和优化建议
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import hashlib
import random
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class SQLAuditRecord:
    """GV$SQL_AUDIT记录数据结构"""
    request_time: datetime
    elapsed_time: float
    queue_time: float
    execution_id: str
    sql_id: str
    query_sql: str
    plan_id: str
    cpu_time: float
    physical_read_time: float
    physical_reads: int
    logical_reads: int
    mem_used: int
    rows_returned: int
    user_name: str
    tenant_name: str
    module: str
    action: str


class OceanBaseSQLAnalyzer:
    """OceanBase SQL性能分析器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.use_real_data = False  # 首版使用Mock数据
        
    def query_sql_audit(self, 
                       database_id: int,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       limit: int = 100,
                       order_by: str = "elapsed_time",
                       order_desc: bool = True) -> List[SQLAuditRecord]:
        """
        查询GV$SQL_AUDIT视图
        首版使用Mock数据，后续可接入真实GV$视图
        """
        if self.use_real_data:
            return self._query_real_sql_audit(database_id, start_time, end_time, limit, order_by, order_desc)
        else:
            return self._generate_mock_sql_audit(database_id, start_time, end_time, limit)
    
    def analyze_slow_queries(self, 
                           database_id: int,
                           threshold_seconds: float = 1.0,
                           hours: int = 24) -> Dict[str, Any]:
        """分析慢查询"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取慢查询数据
        slow_queries = self.query_sql_audit(
            database_id=database_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # 过滤慢查询
        slow_queries = [q for q in slow_queries if q.elapsed_time >= threshold_seconds]
        
        # 分析结果
        analysis = {
            "summary": self._analyze_slow_query_summary(slow_queries),
            "top_slow_queries": self._get_top_slow_queries(slow_queries, 20),
            "performance_patterns": self._analyze_performance_patterns(slow_queries),
            "optimization_suggestions": self._generate_optimization_suggestions(slow_queries),
            "analysis_timestamp": datetime.now().isoformat(),
            "data_source": "mock_gv_sql_audit"
        }
        
        return analysis
    
    def analyze_sql_performance_trends(self, 
                                     database_id: int,
                                     days: int = 7) -> Dict[str, Any]:
        """分析SQL性能趋势"""
        trends = {
            "daily_stats": [],
            "hourly_patterns": {},
            "top_performing_sqls": [],
            "worst_performing_sqls": [],
            "resource_utilization": {},
            "analysis_period": f"{days}天"
        }
        
        # 生成每日统计
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            daily_queries = self._generate_mock_daily_queries(database_id, date)
            
            daily_stats = {
                "date": date.strftime("%Y-%m-%d"),
                "total_queries": len(daily_queries),
                "slow_queries": len([q for q in daily_queries if q.elapsed_time > 1.0]),
                "avg_elapsed_time": sum(q.elapsed_time for q in daily_queries) / len(daily_queries) if daily_queries else 0,
                "max_elapsed_time": max(q.elapsed_time for q in daily_queries) if daily_queries else 0,
                "total_cpu_time": sum(q.cpu_time for q in daily_queries),
                "total_physical_reads": sum(q.physical_reads for q in daily_queries),
                "total_logical_reads": sum(q.logical_reads for q in daily_queries)
            }
            trends["daily_stats"].append(daily_stats)
        
        # 生成小时模式
        trends["hourly_patterns"] = self._analyze_hourly_patterns(database_id, days)
        
        # 生成最佳/最差SQL
        all_queries = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            all_queries.extend(self._generate_mock_daily_queries(database_id, date))
        
        trends["top_performing_sqls"] = self._get_top_performing_sqls(all_queries, 10)
        trends["worst_performing_sqls"] = self._get_worst_performing_sqls(all_queries, 10)
        
        return trends
    
    def analyze_sql_execution_plan(self, sql_text: str) -> Dict[str, Any]:
        """分析SQL执行计划"""
        # 模拟执行计划分析
        plan_analysis = {
            "sql_text": sql_text,
            "estimated_cost": random.randint(100, 10000),
            "estimated_rows": random.randint(100, 1000000),
            "execution_plan": self._generate_mock_execution_plan(sql_text),
            "index_usage": self._analyze_index_usage(sql_text),
            "join_analysis": self._analyze_join_patterns(sql_text),
            "optimization_suggestions": self._generate_plan_optimization_suggestions(sql_text),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return plan_analysis
    
    def generate_sql_optimization_script(self, 
                                       analysis_results: Dict[str, Any]) -> str:
        """生成SQL优化脚本"""
        script_lines = [
            "-- OceanBase SQL优化脚本",
            f"-- 生成时间: {datetime.now().isoformat()}",
            "-- 基于GV$SQL_AUDIT分析结果",
            ""
        ]
        
        # 添加索引建议
        if "index_suggestions" in analysis_results:
            script_lines.extend([
                "-- 索引优化建议",
                "-- ================"
            ])
            for suggestion in analysis_results["index_suggestions"][:5]:
                script_lines.append(f"-- {suggestion['description']}")
                if "create_index_sql" in suggestion:
                    script_lines.append(suggestion["create_index_sql"])
                script_lines.append("")
        
        # 添加SQL重写建议
        if "sql_rewrite_suggestions" in analysis_results:
            script_lines.extend([
                "-- SQL重写建议",
                "-- =============="
            ])
            for suggestion in analysis_results["sql_rewrite_suggestions"][:3]:
                script_lines.extend([
                    f"-- 原SQL: {suggestion.get('original_sql', '')[:100]}...",
                    f"-- 建议: {suggestion.get('suggestion', '')}",
                    f"-- 预期提升: {suggestion.get('expected_improvement', '')}",
                    ""
                ])
        
        # 添加统计信息更新
        script_lines.extend([
            "-- 统计信息更新",
            "-- ==============",
            "-- 建议定期更新统计信息以保持执行计划准确性",
            "-- CALL DBMS_STATS.GATHER_DATABASE_STATS();",
            ""
        ])
        
        return "\n".join(script_lines)
    
    def _query_real_sql_audit(self, 
                            database_id: int,
                            start_time: Optional[datetime],
                            end_time: Optional[datetime],
                            limit: int,
                            order_by: str,
                            order_desc: bool) -> List[SQLAuditRecord]:
        """查询真实的GV$SQL_AUDIT视图"""
        # 这里应该连接OceanBase数据库查询GV$SQL_AUDIT
        # 首版暂不实现，返回空列表
        return []
    
    def _generate_mock_sql_audit(self, 
                               database_id: int,
                               start_time: Optional[datetime],
                               end_time: Optional[datetime],
                               limit: int) -> List[SQLAuditRecord]:
        """生成模拟的GV$SQL_AUDIT数据"""
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now()
        
        # 使用数据库ID作为随机种子确保一致性
        random.seed(database_id)
        
        records = []
        sql_templates = [
            "SELECT * FROM users WHERE user_id = ? AND status = 'active'",
            "SELECT u.*, p.profile_data FROM users u JOIN profiles p ON u.user_id = p.user_id WHERE u.created_at > ?",
            "SELECT COUNT(*) FROM orders WHERE order_date BETWEEN ? AND ? AND status = 'completed'",
            "UPDATE products SET stock_count = stock_count - ? WHERE product_id = ? AND stock_count >= ?",
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
            "DELETE FROM expired_sessions WHERE last_activity < ?",
            "SELECT DISTINCT category FROM products WHERE price > ? ORDER BY category",
            "SELECT AVG(amount) FROM transactions WHERE account_id = ? AND transaction_date >= ?",
            "SELECT * FROM logs WHERE level = 'ERROR' AND timestamp > ? ORDER BY timestamp DESC LIMIT 100",
            "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id HAVING COUNT(*) > ?"
        ]
        
        for i in range(min(limit, 200)):
            # 生成随机时间
            time_diff = (end_time - start_time).total_seconds()
            random_seconds = random.uniform(0, time_diff)
            request_time = start_time + timedelta(seconds=random_seconds)
            
            # 选择SQL模板
            sql_template = random.choice(sql_templates)
            
            # 生成性能数据
            elapsed_time = random.uniform(0.01, 10.0)
            cpu_time = elapsed_time * random.uniform(0.3, 0.9)
            physical_reads = random.randint(0, 10000)
            logical_reads = physical_reads + random.randint(0, 5000)
            
            record = SQLAuditRecord(
                request_time=request_time,
                elapsed_time=elapsed_time,
                queue_time=random.uniform(0.001, 0.1),
                execution_id=f"exec_{i}_{int(request_time.timestamp())}",
                sql_id=hashlib.md5(sql_template.encode()).hexdigest()[:16],
                query_sql=sql_template,
                plan_id=f"plan_{random.randint(1000, 9999)}",
                cpu_time=cpu_time,
                physical_read_time=random.uniform(0.001, 2.0),
                physical_reads=physical_reads,
                logical_reads=logical_reads,
                mem_used=random.randint(1024, 102400),
                rows_returned=random.randint(1, 1000),
                user_name=random.choice(["app_user", "admin", "analyst", "batch_user"]),
                tenant_name="ob_tenant_demo",
                module=random.choice(["web_app", "batch_job", "analytics", "admin_tool"]),
                action=random.choice(["SELECT", "INSERT", "UPDATE", "DELETE"])
            )
            records.append(record)
        
        # 按elapsed_time降序排序
        records.sort(key=lambda x: x.elapsed_time, reverse=True)
        
        return records[:limit]
    
    def _generate_mock_daily_queries(self, database_id: int, date: datetime) -> List[SQLAuditRecord]:
        """生成指定日期的模拟查询数据"""
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        return self._generate_mock_sql_audit(database_id, start_time, end_time, 500)
    
    def _analyze_slow_query_summary(self, slow_queries: List[SQLAuditRecord]) -> Dict[str, Any]:
        """分析慢查询摘要"""
        if not slow_queries:
            return {
                "total_slow_queries": 0,
                "avg_elapsed_time": 0.0,
                "max_elapsed_time": 0.0,
                "total_cpu_time": 0.0,
                "total_physical_reads": 0,
                "total_logical_reads": 0,
                "slow_query_percentage": 0.0
            }
        
        total_queries = len(slow_queries) * 10  # 假设慢查询占总查询的10%
        
        return {
            "total_slow_queries": len(slow_queries),
            "avg_elapsed_time": sum(q.elapsed_time for q in slow_queries) / len(slow_queries),
            "max_elapsed_time": max(q.elapsed_time for q in slow_queries),
            "total_cpu_time": sum(q.cpu_time for q in slow_queries),
            "total_physical_reads": sum(q.physical_reads for q in slow_queries),
            "total_logical_reads": sum(q.logical_reads for q in slow_queries),
            "slow_query_percentage": (len(slow_queries) / total_queries) * 100
        }
    
    def _get_top_slow_queries(self, slow_queries: List[SQLAuditRecord], limit: int) -> List[Dict[str, Any]]:
        """获取最慢的查询"""
        top_queries = []
        for query in slow_queries[:limit]:
            top_queries.append({
                "sql_id": query.sql_id,
                "query_sql": query.query_sql,
                "elapsed_time": query.elapsed_time,
                "cpu_time": query.cpu_time,
                "physical_reads": query.physical_reads,
                "logical_reads": query.logical_reads,
                "rows_returned": query.rows_returned,
                "execution_count": random.randint(1, 100),
                "avg_elapsed_time": query.elapsed_time,
                "optimization_potential": self._calculate_optimization_potential(query)
            })
        return top_queries
    
    def _analyze_performance_patterns(self, slow_queries: List[SQLAuditRecord]) -> Dict[str, Any]:
        """分析性能模式"""
        patterns = {
            "common_operations": {},
            "table_access_patterns": {},
            "join_patterns": {},
            "index_usage_patterns": {},
            "resource_bottlenecks": {}
        }
        
        # 分析常见操作
        operations = {}
        for query in slow_queries:
            op = query.action
            operations[op] = operations.get(op, 0) + 1
        patterns["common_operations"] = operations
        
        # 分析表访问模式
        table_patterns = {}
        for query in slow_queries:
            tables = self._extract_table_names(query.query_sql)
            for table in tables:
                table_patterns[table] = table_patterns.get(table, 0) + 1
        patterns["table_access_patterns"] = table_patterns
        
        # 分析资源瓶颈
        cpu_bottleneck = sum(1 for q in slow_queries if q.cpu_time / q.elapsed_time > 0.8)
        io_bottleneck = sum(1 for q in slow_queries if q.physical_reads > 1000)
        
        patterns["resource_bottlenecks"] = {
            "cpu_bottleneck_queries": cpu_bottleneck,
            "io_bottleneck_queries": io_bottleneck,
            "memory_intensive_queries": sum(1 for q in slow_queries if q.mem_used > 50000)
        }
        
        return patterns
    
    def _generate_optimization_suggestions(self, slow_queries: List[SQLAuditRecord]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []
        
        # 基于CPU瓶颈的建议
        cpu_heavy_queries = [q for q in slow_queries if q.cpu_time / q.elapsed_time > 0.8]
        if cpu_heavy_queries:
            suggestions.append({
                "type": "cpu_optimization",
                "priority": "high",
                "title": "CPU密集型查询优化",
                "description": f"发现{len(cpu_heavy_queries)}个CPU密集型查询",
                "actions": [
                    "检查是否存在全表扫描",
                    "优化JOIN条件和顺序",
                    "考虑添加合适的索引",
                    "使用LIMIT限制结果集"
                ],
                "affected_queries": len(cpu_heavy_queries)
            })
        
        # 基于IO瓶颈的建议
        io_heavy_queries = [q for q in slow_queries if q.physical_reads > 1000]
        if io_heavy_queries:
            suggestions.append({
                "type": "io_optimization",
                "priority": "high",
                "title": "IO密集型查询优化",
                "description": f"发现{len(io_heavy_queries)}个IO密集型查询",
                "actions": [
                    "检查索引使用情况",
                    "优化查询条件减少扫描范围",
                    "考虑分区表设计",
                    "检查统计信息是否过期"
                ],
                "affected_queries": len(io_heavy_queries)
            })
        
        # 基于内存使用的建议
        memory_heavy_queries = [q for q in slow_queries if q.mem_used > 50000]
        if memory_heavy_queries:
            suggestions.append({
                "type": "memory_optimization",
                "priority": "medium",
                "title": "内存使用优化",
                "description": f"发现{len(memory_heavy_queries)}个内存密集型查询",
                "actions": [
                    "检查排序和分组操作",
                    "优化子查询和临时表",
                    "考虑分页处理大数据集",
                    "检查连接池配置"
                ],
                "affected_queries": len(memory_heavy_queries)
            })
        
        return suggestions
    
    def _analyze_hourly_patterns(self, database_id: int, days: int) -> Dict[str, Any]:
        """分析小时模式"""
        hourly_stats = {}
        for hour in range(24):
            hourly_stats[str(hour)] = {
                "avg_queries_per_hour": random.randint(50, 500),
                "avg_elapsed_time": random.uniform(0.1, 2.0),
                "peak_hour": hour in [9, 10, 14, 15, 20, 21],
                "slow_query_ratio": random.uniform(0.05, 0.15)
            }
        return hourly_stats
    
    def _get_top_performing_sqls(self, queries: List[SQLAuditRecord], limit: int) -> List[Dict[str, Any]]:
        """获取性能最好的SQL"""
        # 按执行时间排序，取最快的
        fast_queries = sorted(queries, key=lambda x: x.elapsed_time)[:limit]
        return [{
            "sql_id": q.sql_id,
            "query_sql": q.query_sql,
            "elapsed_time": q.elapsed_time,
            "execution_count": random.randint(10, 1000),
            "efficiency_score": 100 - (q.elapsed_time * 10)
        } for q in fast_queries]
    
    def _get_worst_performing_sqls(self, queries: List[SQLAuditRecord], limit: int) -> List[Dict[str, Any]]:
        """获取性能最差的SQL"""
        # 按执行时间排序，取最慢的
        slow_queries = sorted(queries, key=lambda x: x.elapsed_time, reverse=True)[:limit]
        return [{
            "sql_id": q.sql_id,
            "query_sql": q.query_sql,
            "elapsed_time": q.elapsed_time,
            "execution_count": random.randint(1, 50),
            "efficiency_score": max(0, 100 - (q.elapsed_time * 10))
        } for q in slow_queries]
    
    def _generate_mock_execution_plan(self, sql_text: str) -> List[Dict[str, Any]]:
        """生成模拟执行计划"""
        plan = []
        
        # 根据SQL类型生成不同的执行计划
        if "SELECT" in sql_text.upper():
            plan.extend([
                {
                    "id": 1,
                    "operation": "SELECT",
                    "object_name": "users",
                    "cost": random.randint(100, 1000),
                    "rows": random.randint(100, 10000),
                    "access_predicates": "user_id = ?",
                    "filter_predicates": "status = 'active'"
                }
            ])
            
            if "JOIN" in sql_text.upper():
                plan.append({
                    "id": 2,
                    "operation": "HASH JOIN",
                    "object_name": "profiles",
                    "cost": random.randint(200, 2000),
                    "rows": random.randint(50, 5000),
                    "access_predicates": "user_id = u.user_id"
                })
        
        return plan
    
    def _analyze_index_usage(self, sql_text: str) -> Dict[str, Any]:
        """分析索引使用情况"""
        index_usage = {
            "used_indexes": [],
            "missing_indexes": [],
            "index_effectiveness": "good"
        }
        
        # 简单的索引分析逻辑
        if "WHERE" in sql_text.upper():
            where_clause = sql_text.upper().split("WHERE")[1].split("ORDER BY")[0] if "ORDER BY" in sql_text.upper() else sql_text.upper().split("WHERE")[1]
            
            # 检查常见索引列
            if "user_id" in where_clause:
                index_usage["used_indexes"].append("idx_users_user_id")
            if "created_at" in where_clause:
                index_usage["used_indexes"].append("idx_users_created_at")
            if "status" in where_clause and "user_id" not in where_clause:
                index_usage["missing_indexes"].append("idx_users_status")
        
        return index_usage
    
    def _analyze_join_patterns(self, sql_text: str) -> Dict[str, Any]:
        """分析JOIN模式"""
        join_analysis = {
            "join_count": sql_text.upper().count("JOIN"),
            "join_types": [],
            "join_effectiveness": "good"
        }
        
        if "INNER JOIN" in sql_text.upper():
            join_analysis["join_types"].append("INNER JOIN")
        if "LEFT JOIN" in sql_text.upper():
            join_analysis["join_types"].append("LEFT JOIN")
        if "RIGHT JOIN" in sql_text.upper():
            join_analysis["join_types"].append("RIGHT JOIN")
        
        return join_analysis
    
    def _generate_plan_optimization_suggestions(self, sql_text: str) -> List[Dict[str, Any]]:
        """生成执行计划优化建议"""
        suggestions = []
        
        if "SELECT *" in sql_text.upper():
            suggestions.append({
                "type": "select_optimization",
                "priority": "medium",
                "description": "避免使用SELECT *，只选择需要的列",
                "expected_improvement": "10-30%"
            })
        
        if "LIKE '%" in sql_text:
            suggestions.append({
                "type": "like_optimization",
                "priority": "high",
                "description": "避免前导通配符LIKE查询，考虑全文索引",
                "expected_improvement": "50-80%"
            })
        
        if "ORDER BY" in sql_text.upper() and "LIMIT" not in sql_text.upper():
            suggestions.append({
                "type": "order_by_optimization",
                "priority": "medium",
                "description": "考虑添加LIMIT限制结果集大小",
                "expected_improvement": "20-50%"
            })
        
        return suggestions
    
    def _calculate_optimization_potential(self, query: SQLAuditRecord) -> str:
        """计算优化潜力"""
        if query.elapsed_time > 5.0:
            return "high"
        elif query.elapsed_time > 2.0:
            return "medium"
        else:
            return "low"
    
    def _extract_table_names(self, sql_text: str) -> List[str]:
        """从SQL中提取表名"""
        # 简单的表名提取逻辑
        tables = []
        sql_upper = sql_text.upper()
        
        # 查找FROM子句中的表名
        if "FROM" in sql_upper:
            from_part = sql_upper.split("FROM")[1].split("WHERE")[0] if "WHERE" in sql_upper else sql_upper.split("FROM")[1]
            from_part = from_part.split("JOIN")[0] if "JOIN" in from_part else from_part
            tables.append(from_part.strip().split()[0].lower())
        
        # 查找JOIN子句中的表名
        if "JOIN" in sql_upper:
            join_parts = sql_upper.split("JOIN")[1:]
            for part in join_parts:
                table_name = part.split("ON")[0].strip().split()[0].lower()
                if table_name not in tables:
                    tables.append(table_name)
        
        return tables

