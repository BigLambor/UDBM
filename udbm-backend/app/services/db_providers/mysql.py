"""
MySQL Provider 适配器（首版，基础能力接入）
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import time

from app.models.performance_tuning import SlowQuery
from app.services.performance_tuning.tuning_executor import TuningExecutor
from app.services.performance_tuning.mysql_config_optimizer import MySQLConfigOptimizer


class _MySQLMonitor:
    def __init__(self, session: Session):
        self._session = session

    def dashboard(self, database_id: int, hours: int = 24) -> Dict[str, Any]:
        import random
        import time
        from datetime import datetime, timedelta
        
        # 获取最新指标
        latest = self.latest_metrics(database_id)
        
        # 生成时间序列数据
        metrics_data = []
        base_time = datetime.now() - timedelta(hours=hours)
        
        for i in range(min(hours * 4, 100)):  # 每15分钟一个数据点，最多100个点
            timestamp = base_time + timedelta(minutes=i * 15)
            
            # 基于最新指标生成变化数据
            cpu_base = latest["cpu"]["usage_percent"]
            memory_base = latest["memory"]["usage_percent"]
            qps_base = latest["throughput"]["qps"]
            connections_base = latest["connections"]["active"]
            
            metrics_data.append({
                "timestamp": timestamp.isoformat(),
                "cpu_usage": max(0, min(100, cpu_base + random.uniform(-15, 15))),
                "memory_usage": max(0, min(100, memory_base + random.uniform(-10, 10))),
                "qps": max(0, qps_base + random.uniform(-qps_base * 0.3, qps_base * 0.3)),
                "active_connections": max(0, connections_base + random.randint(-20, 20)),
                "buffer_hit_ratio": max(85, min(100, latest["mysql"]["buffer_pool_hit_ratio"] + random.uniform(-2, 2))),
                "slow_queries": random.randint(0, 10),
                "innodb_buffer_pool_reads": latest["mysql"]["innodb_buffer_pool_reads"] + random.randint(-1000, 1000),
                "threads_running": latest["connections"]["threads_running"] + random.randint(-3, 3),
                "tmp_tables_on_disk": random.randint(0, 20)
            })
        
        # 计算系统健康评分
        health_score = 100.0
        if latest["cpu"]["usage_percent"] > 80:
            health_score -= 15
        if latest["memory"]["usage_percent"] > 85:
            health_score -= 10
        if latest["mysql"]["buffer_pool_hit_ratio"] < 90:
            health_score -= 10
        if latest["connections"]["active"] > latest["connections"]["max_connections"] * 0.8:
            health_score -= 10
        if latest["mysql"]["tmp_tables_on_disk"] > 20:
            health_score -= 5
        if latest["mysql"]["table_lock_wait_ratio"] > 1.0:
            health_score -= 8
        
        health_score = max(30.0, health_score)
        
        # 生成告警
        alerts = self.alerts(database_id)
        
        return {
            "current_stats": {
                "cpu_usage": latest["cpu"]["usage_percent"],
                "memory_usage": latest["memory"]["used_mb"],
                "active_connections": latest["connections"]["active"],
                "qps": latest["throughput"]["qps"],
                "slow_queries_per_hour": latest["throughput"]["slow_queries_per_minute"] * 60,
                
                # MySQL特有统计
                "buffer_pool_hit_ratio": latest["mysql"]["buffer_pool_hit_ratio"],
                "threads_running": latest["connections"]["threads_running"],
                "tmp_tables_on_disk": latest["mysql"]["tmp_tables_on_disk"],
                "table_locks_waited": latest["mysql"]["table_locks_waited"],
                "innodb_deadlocks": latest["mysql"]["innodb_deadlocks"],
                "key_buffer_hit_ratio": latest["mysql"]["key_buffer_hit_ratio"],
                "qcache_hits": latest["mysql"]["qcache_hits"],
                "sort_merge_passes": latest["mysql"]["sort_merge_passes"],
                "created_tmp_disk_tables": latest["mysql"]["created_tmp_disk_tables"],
                
                # 复制状态
                "slave_lag": latest["mysql"]["slave_lag"],
                "slave_sql_running": latest["mysql"]["slave_sql_running"],
                "slave_io_running": latest["mysql"]["slave_io_running"],
                
                # 系统信息
                "uptime": latest["mysql"]["uptime"],
                "questions": latest["mysql"]["questions"],
                "bytes_sent": latest["mysql"]["bytes_sent"],
                "bytes_received": latest["mysql"]["bytes_received"]
            },
            "time_series_data": {
                "metrics": metrics_data
            },
            "alerts": alerts,
            "system_health_score": round(health_score, 2),
            "mysql_specific_metrics": {
                "innodb_metrics": {
                    "buffer_pool_reads": latest["mysql"]["innodb_buffer_pool_reads"],
                    "buffer_pool_read_requests": latest["mysql"]["innodb_buffer_pool_read_requests"],
                    "buffer_pool_pages_data": latest["mysql"]["innodb_buffer_pool_pages_data"],
                    "buffer_pool_pages_dirty": latest["mysql"]["innodb_buffer_pool_pages_dirty"],
                    "buffer_pool_pages_free": latest["mysql"]["innodb_buffer_pool_pages_free"],
                    "rows_read": latest["mysql"]["innodb_rows_read"],
                    "rows_inserted": latest["mysql"]["innodb_rows_inserted"],
                    "rows_updated": latest["mysql"]["innodb_rows_updated"],
                    "rows_deleted": latest["mysql"]["innodb_rows_deleted"]
                },
                "query_cache_metrics": {
                    "qcache_hits": latest["mysql"]["qcache_hits"],
                    "qcache_inserts": latest["mysql"]["qcache_inserts"],
                    "qcache_not_cached": latest["mysql"]["qcache_not_cached"],
                    "qcache_lowmem_prunes": latest["mysql"]["qcache_lowmem_prunes"]
                },
                "table_metrics": {
                    "created_tmp_tables": latest["mysql"]["created_tmp_tables"],
                    "created_tmp_disk_tables": latest["mysql"]["created_tmp_disk_tables"],
                    "table_locks_immediate": latest["mysql"]["table_locks_immediate"],
                    "table_locks_waited": latest["mysql"]["table_locks_waited"]
                },
                "myisam_metrics": {
                    "key_reads": latest["mysql"]["key_reads"],
                    "key_read_requests": latest["mysql"]["key_read_requests"],
                    "key_writes": latest["mysql"]["key_writes"],
                    "key_write_requests": latest["mysql"]["key_write_requests"]
                }
            },
            "data_source": "enhanced_mock_data",
            "generated_at": datetime.now().isoformat()
        }

    def collect_metrics(self, database_id: int) -> List[Dict[str, Any]]:
        # 预留：通过 SHOW GLOBAL STATUS/VARIABLES + performance_schema 采集
        ts = time.time()
        return [
            {"database_id": database_id, "metric_type": "connections", "metric_name": "threads_running", "metric_value": 12.0, "unit": "count", "timestamp": ts, "tags": "{}", "metadata": "{}"},
        ]

    def save_metrics(self, metrics: List[Dict[str, Any]]):
        # 复用 PG 的保存逻辑需要 SystemMonitor，这里避免耦合：直接不落库（首版）
        return []

    def history(self, database_id: int, metric_type: str, hours: int = 24):
        return []

    def latest_metrics(self, database_id: int) -> Dict[str, Any]:
        import random
        import time
        
        # 生成更丰富的MySQL特有指标
        buffer_pool_hit_ratio = round(random.uniform(88.0, 99.5), 2)
        innodb_buffer_pool_reads = random.randint(50000, 500000)
        innodb_buffer_pool_read_requests = random.randint(10000000, 100000000)
        
        return {
            "cpu": {
                "usage_percent": round(random.uniform(30.0, 80.0), 2), 
                "cores": random.choice([4, 8, 16, 32]), 
                "load_average": [round(random.uniform(0.5, 3.0), 2) for _ in range(3)]
            },
            "memory": {
                "total_mb": random.choice([8192, 16384, 32768, 65536]), 
                "used_mb": random.randint(3000, 12000), 
                "available_mb": random.randint(2000, 8000), 
                "usage_percent": round(random.uniform(40.0, 85.0), 2)
            },
            "connections": {
                "active": random.randint(15, 150), 
                "idle": random.randint(20, 80), 
                "waiting": random.randint(0, 10), 
                "max_connections": random.choice([100, 300, 500, 1000]),
                "threads_connected": random.randint(25, 200),
                "threads_running": random.randint(2, 20),
                "threads_cached": random.randint(10, 50),
                "aborted_connects": random.randint(0, 100)
            },
            "throughput": {
                "qps": round(random.uniform(200.0, 5000.0), 2), 
                "tps": round(random.uniform(100.0, 2000.0), 2), 
                "slow_queries_per_minute": round(random.uniform(0.1, 10.0), 2),
                "com_select": random.randint(100000, 10000000),
                "com_insert": random.randint(10000, 1000000),
                "com_update": random.randint(5000, 500000),
                "com_delete": random.randint(1000, 100000)
            },
            "mysql": {
                # InnoDB 缓冲池指标
                "buffer_pool_hit_ratio": buffer_pool_hit_ratio,
                "innodb_buffer_pool_reads": innodb_buffer_pool_reads,
                "innodb_buffer_pool_read_requests": innodb_buffer_pool_read_requests,
                "innodb_buffer_pool_pages_data": random.randint(50000, 200000),
                "innodb_buffer_pool_pages_dirty": random.randint(1000, 20000),
                "innodb_buffer_pool_pages_free": random.randint(10000, 100000),
                "innodb_buffer_pool_pages_total": random.randint(100000, 500000),
                
                # 查询缓存指标（MySQL 5.7及以下）
                "qcache_hits": random.randint(1000000, 50000000),
                "qcache_inserts": random.randint(100000, 5000000),
                "qcache_not_cached": random.randint(50000, 1000000),
                "qcache_lowmem_prunes": random.randint(1000, 50000),
                
                # 临时表指标
                "tmp_tables_on_disk": random.randint(0, 50),
                "created_tmp_tables": random.randint(10000, 500000),
                "created_tmp_disk_tables": random.randint(1000, 50000),
                
                # 索引和排序指标
                "filesort": random.randint(5, 100),
                "sort_merge_passes": random.randint(100, 10000),
                "sort_range": random.randint(10000, 500000),
                "sort_rows": random.randint(1000000, 50000000),
                "sort_scan": random.randint(5000, 200000),
                
                # MyISAM 键缓存指标
                "key_reads": random.randint(100000, 1000000),
                "key_read_requests": random.randint(10000000, 100000000),
                "key_writes": random.randint(50000, 500000),
                "key_write_requests": random.randint(5000000, 50000000),
                "key_buffer_hit_ratio": round(100.0 - (innodb_buffer_pool_reads / max(innodb_buffer_pool_read_requests, 1)) * 100, 2),
                
                # 锁和表指标
                "table_locks_immediate": random.randint(1000000, 10000000),
                "table_locks_waited": random.randint(100, 5000),
                "table_lock_wait_ratio": round(random.uniform(0.01, 2.0), 3),
                
                # InnoDB 事务和锁指标
                "innodb_rows_read": random.randint(100000000, 10000000000),
                "innodb_rows_inserted": random.randint(1000000, 100000000),
                "innodb_rows_updated": random.randint(500000, 50000000),
                "innodb_rows_deleted": random.randint(100000, 10000000),
                "innodb_deadlocks": random.randint(0, 100),
                
                # 网络和处理指标
                "bytes_received": random.randint(1000000000, 100000000000),
                "bytes_sent": random.randint(500000000, 50000000000),
                "questions": random.randint(10000000, 1000000000),
                "uptime": random.randint(86400, 86400 * 365),  # 1天到1年
                
                # 复制指标（如果启用）
                "slave_lag": random.randint(0, 30) if random.choice([True, False]) else None,
                "slave_sql_running": random.choice(['Yes', 'No', None]),
                "slave_io_running": random.choice(['Yes', 'No', None]),
                
                # 性能schema指标
                "performance_schema_enabled": random.choice([True, False]),
                "events_statements_summary_digest_rows": random.randint(1000, 50000) if random.choice([True, False]) else None
            },
            "timestamp": time.time(),
            "data_source": "enhanced_mock_data"
        }

    def alerts(self, database_id: int) -> List[Dict[str, Any]]:
        import datetime
        m = self.latest_metrics(database_id)
        alerts: List[Dict[str, Any]] = []
        current_time = datetime.datetime.now().isoformat()
        
        # 连接数告警
        if m["connections"]["active"] > m["connections"]["max_connections"] * 0.85:
            alerts.append({
                "level": "warning", 
                "type": "high_connections", 
                "message": f"连接使用率偏高: {m['connections']['active']}/{m['connections']['max_connections']}",
                "timestamp": current_time
            })
        
        # CPU使用率告警
        if m["cpu"]["usage_percent"] > 80:
            alerts.append({
                "level": "critical" if m["cpu"]["usage_percent"] > 90 else "warning",
                "type": "high_cpu",
                "message": f"CPU使用率过高: {m['cpu']['usage_percent']:.1f}%",
                "timestamp": current_time
            })
        
        # 内存使用率告警
        if m["memory"]["usage_percent"] > 85:
            alerts.append({
                "level": "critical" if m["memory"]["usage_percent"] > 95 else "warning",
                "type": "high_memory",
                "message": f"内存使用率过高: {m['memory']['usage_percent']:.1f}%",
                "timestamp": current_time
            })
        
        # InnoDB缓冲池命中率告警
        if m["mysql"]["buffer_pool_hit_ratio"] < 90:
            alerts.append({
                "level": "warning" if m["mysql"]["buffer_pool_hit_ratio"] > 85 else "critical",
                "type": "low_buffer_hit_ratio",
                "message": f"InnoDB缓冲池命中率偏低: {m['mysql']['buffer_pool_hit_ratio']:.2f}%",
                "timestamp": current_time
            })
        
        # 临时表过多告警
        if m["mysql"]["tmp_tables_on_disk"] > 20:
            alerts.append({
                "level": "warning",
                "type": "high_tmp_tables",
                "message": f"磁盘临时表过多: {m['mysql']['tmp_tables_on_disk']}个/小时",
                "timestamp": current_time
            })
        
        # 表锁等待告警
        if m["mysql"]["table_lock_wait_ratio"] > 1.0:
            alerts.append({
                "level": "warning",
                "type": "table_lock_contention",
                "message": f"表锁等待比率过高: {m['mysql']['table_lock_wait_ratio']:.3f}%",
                "timestamp": current_time
            })
        
        # 死锁告警
        if m["mysql"]["innodb_deadlocks"] > 50:
            alerts.append({
                "level": "warning",
                "type": "high_deadlocks",
                "message": f"InnoDB死锁频繁: {m['mysql']['innodb_deadlocks']}次",
                "timestamp": current_time
            })
        
        # 慢查询告警
        if m["throughput"]["slow_queries_per_minute"] > 5:
            alerts.append({
                "level": "warning",
                "type": "high_slow_queries",
                "message": f"慢查询过多: {m['throughput']['slow_queries_per_minute']:.1f}次/分钟",
                "timestamp": current_time
            })
        
        # 复制延迟告警
        if m["mysql"]["slave_lag"] is not None and m["mysql"]["slave_lag"] > 10:
            alerts.append({
                "level": "critical" if m["mysql"]["slave_lag"] > 30 else "warning",
                "type": "replication_lag",
                "message": f"主从复制延迟: {m['mysql']['slave_lag']}秒",
                "timestamp": current_time
            })
        
        # 复制状态告警
        if m["mysql"]["slave_sql_running"] == 'No':
            alerts.append({
                "level": "critical",
                "type": "replication_broken",
                "message": "MySQL主从复制SQL线程停止",
                "timestamp": current_time
            })
        
        if m["mysql"]["slave_io_running"] == 'No':
            alerts.append({
                "level": "critical",
                "type": "replication_broken",
                "message": "MySQL主从复制IO线程停止",
                "timestamp": current_time
            })
        
        # MyISAM键缓存命中率告警
        if m["mysql"]["key_buffer_hit_ratio"] < 95:
            alerts.append({
                "level": "info",
                "type": "low_key_buffer_hit_ratio",
                "message": f"MyISAM键缓存命中率偏低: {m['mysql']['key_buffer_hit_ratio']:.2f}%",
                "timestamp": current_time
            })
        
        return alerts

    def recommendations(self, database_id: int) -> List[Dict[str, Any]]:
        return [
            {"category": "memory", "priority": "high", "title": "提升InnoDB缓冲池", "description": "提升缓存命中率，降低IO"},
        ]

    def report(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        return {"period": f"{days}天", "generated_at": "", "summary": {"avg_qps": 520}}

    def start_realtime(self, database_id: int, interval_seconds: int = 60) -> Dict[str, Any]:
        return {"database_id": database_id, "interval_seconds": interval_seconds, "monitoring_started": True}

    def stop_realtime(self, database_id: int) -> Dict[str, Any]:
        return {"database_id": database_id, "monitoring_stopped": True}

    def status(self, database_id: int) -> Dict[str, Any]:
        return {"database_id": database_id, "monitoring_active": True, "collection_interval_seconds": 60}


class _MySQLSlowQueries:
    def __init__(self, session: Session):
        self._session = session

    def _get_mysql_connection(self):
        """获取MySQL数据库连接"""
        from sqlalchemy import create_engine
        return create_engine(
            f"mysql+pymysql://root:udbm_root_password@localhost:3306/udbm_mysql_demo",
            echo=False
        )

    def list(self, database_id: int, limit: int, offset: int):
        # 连接到MySQL数据库查询慢查询数据
        from sqlalchemy import create_engine, text
        from app.core.config import settings
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"MySQL Provider: Querying database_id={database_id}, limit={limit}, offset={offset}")
        
        # 创建MySQL连接
        mysql_engine = create_engine(
            f"mysql+pymysql://root:udbm_root_password@localhost:3306/udbm_mysql_demo",
            echo=False
        )
        
        with mysql_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, database_id, query_text, query_hash, execution_time, lock_time,
                       rows_sent, rows_examined, timestamp, user_host, sql_command, status,
                       analysis_result, optimization_suggestions, created_at, updated_at
                FROM slow_queries 
                WHERE database_id = :db_id 
                ORDER BY timestamp DESC 
                LIMIT :limit OFFSET :offset
            """), {"db_id": database_id, "limit": limit, "offset": offset})
            
            rows = result.fetchall()
            
            # 转换为SlowQuery对象
            slow_queries = []
            for row in rows:
                sq = SlowQuery(
                    id=row[0],
                    database_id=row[1],
                    query_text=row[2],
                    query_hash=row[3],
                    execution_time=row[4],
                    lock_time=row[5],
                    rows_sent=row[6],
                    rows_examined=row[7],
                    timestamp=row[8],
                    user_host=row[9],
                    sql_command=row[10],
                    status=row[11],
                    analysis_result=row[12],
                    optimization_suggestions=row[13],
                    created_at=row[14],
                    updated_at=row[15]
                )
                slow_queries.append(sq)
            
            return slow_queries

    def capture(self, database_id: int, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        # 首版占位：依赖 performance_schema digest 实现，暂时返回空
        return []

    def save(self, slow_query_data: Dict[str, Any]):
        sq = SlowQuery(**slow_query_data)
        self._session.add(sq)
        self._session.commit()
        self._session.refresh(sq)
        return sq

    def analyze_text(self, query_text: str, execution_time: float, rows_examined: int) -> Dict[str, Any]:
        # 复用现有 PG 分析规则思想：返回基础建议
        suggestions: List[Dict[str, Any]] = []
        q = query_text.upper()
        if "JOIN" in q:
            suggestions.append({"type": "join_index", "description": "为 JOIN 列添加索引", "impact": "high", "estimated_improvement": "40-70%"})
        if "ORDER BY" in q:
            suggestions.append({"type": "order_by_index", "description": "为排序列添加索引", "impact": "medium", "estimated_improvement": "30-50%"})
        if "LIKE '%" in query_text or "LIKE \"%" in query_text:
            suggestions.append({"type": "fulltext_or_ngram", "description": "使用FULLTEXT或n-gram索引", "impact": "high", "estimated_improvement": "60-85%"})
        return {"query_analysis": {"complexity_score": 50, "efficiency_score": 60, "performance_rating": "fair"}, "suggestions": suggestions[:5], "priority_score": 70, "estimated_improvement": "50%"}

    def patterns(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        """分析MySQL慢查询模式和热点表"""
        from sqlalchemy import create_engine, text
        from datetime import datetime, timedelta
        import re
        from collections import defaultdict
        
        # 创建MySQL连接
        mysql_engine = create_engine(
            f"mysql+pymysql://root:udbm_root_password@localhost:3306/udbm_mysql_demo",
            echo=False
        )
        
        with mysql_engine.connect() as conn:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取慢查询数据
            result = conn.execute(text("""
                SELECT 
                    query_text,
                    execution_time,
                    sql_command
                FROM slow_queries 
                WHERE database_id = :db_id 
                AND created_at >= :start_date 
                AND created_at <= :end_date
                ORDER BY created_at DESC
            """), {
                "db_id": database_id,
                "start_date": start_date,
                "end_date": end_date
            })
            
            queries = result.fetchall()
            
            if not queries or len(queries) == 0:
                # 没有数据时返回空结果
                return {
                    "total_slow_queries": 0,
                    "avg_execution_time": 0.0,
                    "most_common_patterns": [],
                    "top_tables": [],
                    "recommendations": ["暂无慢查询数据，建议开启MySQL慢查询日志"]
                }
            
            # 分析查询模式
            patterns = defaultdict(lambda: {"count": 0, "total_time": 0.0})
            table_usage = defaultdict(lambda: {"count": 0, "total_time": 0.0})
            
            total_queries = len(queries)
            total_time = 0.0
            
            for query_row in queries:
                query_text = query_row[0]
                execution_time = query_row[1]
                sql_command = query_row[2] or "UNKNOWN"
                
                total_time += execution_time
                
                # 提取查询模式
                pattern = self._extract_query_pattern(query_text, sql_command)
                patterns[pattern]["count"] += 1
                patterns[pattern]["total_time"] += execution_time
                
                # 提取表名
                tables = self._extract_table_names(query_text)
                for table in tables:
                    table_usage[table]["count"] += 1
                    table_usage[table]["total_time"] += execution_time
            
            # 格式化查询模式
            most_common_patterns = []
            for pattern, data in patterns.items():
                avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
                impact_score = self._calculate_pattern_impact(pattern, data)
                most_common_patterns.append({
                    "pattern": pattern,
                    "count": data["count"],
                    "avg_time": round(avg_time, 2),
                    "impact_score": impact_score
                })
            
            # 按影响分数排序
            most_common_patterns.sort(key=lambda x: x["impact_score"], reverse=True)
            
            # 格式化热点表
            top_tables = []
            for table, usage in table_usage.items():
                avg_time = usage["total_time"] / usage["count"] if usage["count"] > 0 else 0
                top_tables.append({
                    "table": table,
                    "query_count": usage["count"],
                    "avg_time": round(avg_time, 2),
                    "total_time": round(usage["total_time"], 2)
                })
            
            # 按总时间排序
            top_tables.sort(key=lambda x: x["total_time"], reverse=True)
            
            # 生成建议
            recommendations = []
            if most_common_patterns:
                top_pattern = most_common_patterns[0]
                if "JOIN" in top_pattern["pattern"]:
                    recommendations.append("优化JOIN查询，为关联字段添加索引")
                if "ORDER BY" in top_pattern["pattern"]:
                    recommendations.append("为排序字段添加索引以提升性能")
                if "WHERE" in top_pattern["pattern"]:
                    recommendations.append("为WHERE条件字段添加索引")
            
            if top_tables:
                top_table = top_tables[0]
                recommendations.append(f"重点优化表 {top_table['table']} 的查询性能")
            
            if not recommendations:
                recommendations = [
                    "为高频查询的WHERE条件列添加索引",
                    "定期执行ANALYZE TABLE更新表统计信息",
                    "考虑使用查询缓存提升性能"
                ]
            
            avg_execution_time = total_time / total_queries if total_queries > 0 else 0.0
            
            return {
                "total_slow_queries": total_queries,
                "avg_execution_time": round(avg_execution_time, 2),
                "most_common_patterns": most_common_patterns[:10],
                "top_tables": top_tables[:10],
                "recommendations": recommendations
            }
    
    def _extract_query_pattern(self, query_text: str, sql_command: str) -> str:
        """提取MySQL查询模式"""
        query_upper = query_text.upper()
        
        if sql_command == "SELECT":
            if "JOIN" in query_upper and "ORDER BY" in query_upper:
                return "SELECT with JOIN and ORDER BY"
            elif "JOIN" in query_upper:
                return "SELECT with JOIN"
            elif "ORDER BY" in query_upper:
                return "SELECT with ORDER BY"
            elif "GROUP BY" in query_upper:
                return "SELECT with GROUP BY"
            elif "LIKE" in query_upper:
                return "SELECT with LIKE"
            elif "IN (" in query_upper:
                return "SELECT with IN"
            else:
                return "Simple SELECT"
        elif sql_command == "UPDATE":
            if "WHERE" in query_upper and "IN (" in query_upper:
                return "UPDATE with WHERE IN"
            elif "WHERE" in query_upper:
                return "UPDATE with WHERE"
            else:
                return "Simple UPDATE"
        elif sql_command == "DELETE":
            if "WHERE" in query_upper:
                return "DELETE with WHERE"
            else:
                return "Simple DELETE"
        elif sql_command == "INSERT":
            if "SELECT" in query_upper:
                return "INSERT with SELECT"
            else:
                return "Simple INSERT"
        else:
            return f"{sql_command} query"
    
    def _extract_table_names(self, query_text: str) -> List[str]:
        """提取查询中的表名"""
        import re
        query_upper = query_text.upper()
        
        # 匹配 FROM、JOIN、UPDATE、INSERT INTO、DELETE FROM 后的表名
        patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)'
        ]
        
        tables = []
        for pattern in patterns:
            matches = re.findall(pattern, query_upper)
            tables.extend(matches)
        
        # 去重并返回小写表名
        return list(set(table.lower() for table in tables))
    
    def _calculate_pattern_impact(self, pattern: str, data: Dict[str, Any]) -> int:
        """计算查询模式的影响程度"""
        base_score = data["count"] * 10  # 数量权重
        time_score = data["total_time"] * 5  # 执行时间权重
        
        # 模式复杂度权重
        complexity_multipliers = {
            "SELECT with JOIN and ORDER BY": 1.5,
            "UPDATE with WHERE IN": 1.4,
            "DELETE with WHERE": 1.3,
            "SELECT with JOIN": 1.3,
            "SELECT with LIKE": 1.2,
            "INSERT with SELECT": 1.1
        }
        
        multiplier = complexity_multipliers.get(pattern, 1.0)
        
        return int((base_score + time_score) * multiplier)

    def statistics(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        # 连接到MySQL数据库查询统计信息
        from sqlalchemy import create_engine, text
        from datetime import datetime, timedelta
        
        # 创建MySQL连接
        mysql_engine = create_engine(
            f"mysql+pymysql://root:udbm_root_password@localhost:3306/udbm_mysql_demo",
            echo=False
        )
        
        with mysql_engine.connect() as conn:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取慢查询统计
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_queries,
                    COUNT(CASE WHEN execution_time > 1.0 THEN 1 END) as slow_queries,
                    AVG(execution_time) as avg_execution_time,
                    MAX(execution_time) as max_execution_time
                FROM slow_queries 
                WHERE database_id = :db_id 
                AND created_at >= :start_date 
                AND created_at <= :end_date
            """), {
                "db_id": database_id, 
                "start_date": start_date, 
                "end_date": end_date
            })
            
            stats = result.fetchone()
            
            if stats and stats[0] is not None:
                total_queries = stats[0] or 0
                slow_queries = stats[1] or 0
                avg_execution_time = stats[2] or 0.0
                max_execution_time = stats[3] or 0.0
                
                # 计算慢查询占比
                slow_query_percentage = (slow_queries / total_queries * 100) if total_queries > 0 else 0.0
                
                # 计算每秒查询数（基于时间范围）
                queries_per_second = total_queries / (days * 24 * 3600) if days > 0 else 0.0
                
                # 判断趋势（简化版本，基于慢查询占比）
                trend = "stable"
                if slow_query_percentage > 10:
                    trend = "worsening"
                elif slow_query_percentage < 2:
                    trend = "improving"
            else:
                total_queries = 0
                slow_queries = 0
                avg_execution_time = 0.0
                max_execution_time = 0.0
                slow_query_percentage = 0.0
                queries_per_second = 0.0
                trend = "stable"
            
            return {
                "period": f"{days}天",
                "total_queries": total_queries,
                "slow_queries": slow_queries,
                "slow_query_percentage": round(slow_query_percentage, 2),
                "avg_execution_time": round(avg_execution_time, 3),
                "max_execution_time": round(max_execution_time, 3),
                "queries_per_second": round(queries_per_second, 2),
                "trend": trend
            }


class _MySQLConfig:
    def __init__(self, session: Session):
        self._o = MySQLConfigOptimizer(session)

    def analyze_config(self, database_id: int) -> Dict[str, Any]:
        return self._o.analyze_configuration(database_id)

    def maintenance_strategy(self, database_id: int) -> Dict[str, Any]:
        return self._o.maintenance_strategy(database_id)

    def optimize_memory(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        return self._o.optimize_memory_settings(system_info)

    def optimize_connections(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        return self._o.optimize_connection_settings(workload_info)

    def generate_tuning_script(self, analysis_results: Dict[str, Any]) -> str:
        return self._o.generate_performance_tuning_script(analysis_results)


class _MySQLExecutor:
    def __init__(self, session: Session):
        self._e = TuningExecutor(session)

    def execute_task(self, task_id: int) -> Dict[str, Any]:
        return self._e.execute_task(task_id)

    def stats(self, database_id: Optional[int] = None) -> Dict[str, Any]:
        return self._e.get_task_statistics(database_id)


class MySQLProvider:
    def __init__(self, session: Session):
        self.monitor = _MySQLMonitor(session)
        self.slow_queries = _MySQLSlowQueries(session)
        self.optimizer = _MySQLConfig(session)
        self.executor = _MySQLExecutor(session)

