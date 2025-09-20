"""
OceanBase Provider 适配器（首版，专业版指标与建议）
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.performance_tuning.tuning_executor import TuningExecutor
from app.services.performance_tuning.oceanbase_config_optimizer import OceanBaseConfigOptimizer


class _OBMonitor:
    def __init__(self, session: Session):
        self._session = session

    def dashboard(self, database_id: int, hours: int = 24) -> Dict[str, Any]:
        import random
        from datetime import datetime, timedelta

        latest = self.latest_metrics(database_id)

        # 生成时间序列数据（每15分钟一个点，最多100个）
        metrics_data = []
        base_time = datetime.now() - timedelta(hours=hours)
        for i in range(min(hours * 4, 100)):
            timestamp = base_time + timedelta(minutes=i * 15)
            metrics_data.append({
                "timestamp": timestamp.isoformat(),
                "cpu_usage": max(0, min(100, latest["cpu"]["usage_percent"] + random.uniform(-10, 10))),
                "memory_usage": max(1024, latest["memory"]["used_mb"] + random.uniform(-256, 256)),
                "qps": max(0, latest["throughput"]["qps"] + random.uniform(-latest["throughput"]["qps"] * 0.25, latest["throughput"]["qps"] * 0.25)),
                "active_connections": max(0, latest["connections"]["active"] + random.randint(-10, 10)),
                "buffer_hit_ratio": max(80, min(100, latest["oceanbase"]["plan_cache_hit_ratio"] + random.uniform(-1.5, 1.5))),
                "slow_queries": random.randint(0, 8),
                "rpc_queue": max(0, latest["oceanbase"]["rpc_queue_len"] + random.randint(-5, 5)),
                "major_compaction_progress": max(0, min(100, latest["oceanbase"]["major_compaction_progress"] + random.uniform(-2, 2)))
            })

        # 健康评分（基于核心指标权重）
        score = 100.0
        if latest["cpu"]["usage_percent"] > 80:
            score -= 12
        if latest["memory"]["usage_percent"] > 85:
            score -= 12
        if latest["oceanbase"]["plan_cache_hit_ratio"] < 90:
            score -= 10
        if latest["oceanbase"]["rpc_queue_len"] > 20:
            score -= 8
        if latest["connections"]["active"] > latest["connections"]["max_connections"] * 0.8:
            score -= 8
        if latest["oceanbase"]["major_compaction_progress"] < 90:
            score -= 5
        score = max(30.0, score)

        alerts = self.alerts(database_id)

        return {
            "current_stats": {
                "cpu_usage": latest["cpu"]["usage_percent"],
                "memory_usage": latest["memory"]["used_mb"],
                "active_connections": latest["connections"]["active"],
                "qps": latest["throughput"]["qps"],
                "slow_queries_per_hour": latest["throughput"]["slow_queries_per_minute"] * 60,
                # OceanBase特有
                "plan_cache_hit_ratio": latest["oceanbase"]["plan_cache_hit_ratio"],
                "rpc_queue_len": latest["oceanbase"]["rpc_queue_len"],
                "major_compaction_progress": latest["oceanbase"]["major_compaction_progress"],
                "tenant_mem_used_mb": latest["oceanbase"]["tenant_mem_used_mb"],
                "memstore_used_mb": latest["oceanbase"]["memstore_used_mb"],
                "tablet_count": latest["oceanbase"]["tablet_count"],
            },
            "time_series_data": {"metrics": metrics_data},
            "alerts": alerts,
            "system_health_score": round(score, 2),
            "oceanbase_specific_metrics": latest["oceanbase"],
            "data_source": "enhanced_mock_data",
            "generated_at": datetime.now().isoformat(),
        }

    def collect_metrics(self, database_id: int) -> List[Dict[str, Any]]:
        # 首版：直接返回空，后续通过GV$视图采集
        return []

    def save_metrics(self, metrics: List[Dict[str, Any]]):
        # 首版：不落库
        return []

    def history(self, database_id: int, metric_type: str, hours: int = 24):
        return []

    def latest_metrics(self, database_id: int) -> Dict[str, Any]:
        import random
        import hashlib
        from datetime import datetime

        seed = int(hashlib.md5(f"ob_{database_id}_{datetime.now().hour}".encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)

        qps = round(random.uniform(300.0, 6000.0), 2)
        plan_cache_hit = round(random.uniform(88.0, 99.5), 2)
        rpc_queue = random.randint(0, 25)
        major_compaction = round(random.uniform(75.0, 100.0), 1)
        tenant_mem_used = random.randint(2048, 16384)
        memstore_used = random.randint(512, 4096)
        tablet_count = random.randint(2000, 20000)

        return {
            "cpu": {
                "usage_percent": round(random.uniform(30.0, 85.0), 2),
                "cores": random.choice([8, 16, 32]),
                "load_average": [round(random.uniform(0.5, 3.5), 2) for _ in range(3)],
            },
            "memory": {
                "total_mb": random.choice([16384, 32768, 65536, 131072]),
                "used_mb": tenant_mem_used,
                "available_mb": max(1024, random.randint(2048, 8192)),
                "usage_percent": round(random.uniform(40.0, 90.0), 2),
            },
            "connections": {
                "active": random.randint(20, 180),
                "idle": random.randint(20, 100),
                "waiting": random.randint(0, 15),
                "max_connections": random.choice([256, 512, 1024]),
            },
            "throughput": {
                "qps": qps,
                "tps": round(qps * random.uniform(0.4, 0.8), 2),
                "slow_queries_per_minute": round(random.uniform(0.1, 6.0), 2),
            },
            "oceanbase": {
                "plan_cache_hit_ratio": plan_cache_hit,
                "plan_cache_mem_used_mb": random.randint(256, 4096),
                "plan_cache_mem_limit_mb": random.choice([4096, 8192, 16384]),
                "rpc_queue_len": rpc_queue,
                "major_compaction_progress": major_compaction,
                "minor_compaction_pending": random.randint(0, 50),
                "tenant_mem_used_mb": tenant_mem_used,
                "memstore_used_mb": memstore_used,
                "tablet_count": tablet_count,
                "ls_count": random.randint(8, 128),
                "log_disk_usage_percent": round(random.uniform(20.0, 85.0), 2),
            },
            "data_source": "enhanced_mock_data",
        }

    def alerts(self, database_id: int) -> List[Dict[str, Any]]:
        import datetime
        m = self.latest_metrics(database_id)
        alerts: List[Dict[str, Any]] = []
        ts = datetime.datetime.now().isoformat()

        if m["oceanbase"]["plan_cache_hit_ratio"] < 90:
            alerts.append({
                "level": "warning",
                "type": "plan_cache_low_hit_ratio",
                "message": f"计划缓存命中率偏低: {m['oceanbase']['plan_cache_hit_ratio']:.2f}%",
                "timestamp": ts,
            })

        if m["oceanbase"]["rpc_queue_len"] > 20:
            alerts.append({
                "level": "critical",
                "type": "high_rpc_queue",
                "message": f"RPC 队列长度过高: {m['oceanbase']['rpc_queue_len']}",
                "timestamp": ts,
            })

        if m["oceanbase"]["log_disk_usage_percent"] > 85:
            alerts.append({
                "level": "critical",
                "type": "log_disk_usage_high",
                "message": f"日志盘使用率过高: {m['oceanbase']['log_disk_usage_percent']:.1f}%",
                "timestamp": ts,
            })

        if m["oceanbase"]["major_compaction_progress"] < 80:
            alerts.append({
                "level": "info",
                "type": "compaction_incomplete",
                "message": f"本轮Major Compaction进度: {m['oceanbase']['major_compaction_progress']:.1f}%",
                "timestamp": ts,
            })

        return alerts

    def recommendations(self, database_id: int) -> List[Dict[str, Any]]:
        m = self.latest_metrics(database_id)
        recs: List[Dict[str, Any]] = []

        if m["oceanbase"]["plan_cache_hit_ratio"] < 92:
            recs.append({
                "category": "sql/plan_cache",
                "priority": "high",
                "title": "提高计划缓存命中率",
                "actions": [
                    "合并SQL常量，减少硬解析",
                    "使用Outline/Hint固定稳定计划",
                    "关注热点SQL，优化谓词与索引"
                ],
            })
        if m["oceanbase"]["rpc_queue_len"] > 15:
            recs.append({
                "category": "rpc",
                "priority": "high",
                "title": "降低RPC队列堆积",
                "actions": [
                    "检查合并任务与日志刷盘是否挤占IO",
                    "评估并发，适当扩容Unit CPU/IO",
                ],
            })
        if m["oceanbase"]["major_compaction_progress"] < 90:
            recs.append({
                "category": "compaction",
                "priority": "medium",
                "title": "加速Compaction",
                "actions": [
                    "在业务低峰触发合并",
                    "调整合并并发度、盘类型匹配",
                ],
            })
        return recs

    def report(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        from datetime import datetime
        return {
            "period": f"{days}天",
            "generated_at": datetime.now().isoformat(),
            "summary": {"avg_qps": 1200, "avg_plan_cache_hit": 95.2},
        }

    def start_realtime(self, database_id: int, interval_seconds: int = 60) -> Dict[str, Any]:
        return {"database_id": database_id, "interval_seconds": interval_seconds, "monitoring_started": True}

    def stop_realtime(self, database_id: int) -> Dict[str, Any]:
        return {"database_id": database_id, "monitoring_stopped": True}

    def status(self, database_id: int) -> Dict[str, Any]:
        return {
            "database_id": database_id,
            "monitoring_active": True,
            "collection_interval_seconds": 60,
            "metrics_collected_today": 1200,
            "alerts_today": 2,
        }


class _OBSlowQueries:
    def __init__(self, session: Session):
        self._session = session

    def list(self, database_id: int, limit: int, offset: int):
        # 首版：返回空列表（OceanBase慢SQL建议通过 GV$OB_SQL_AUDIT 在线查询）
        return []

    def capture(self, database_id: int, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        # 预留：调用 GV$OB_SQL_AUDIT 捕获
        return []

    def save(self, slow_query_data: Dict[str, Any]):
        # 预留：将外部采集写入平台库
        return slow_query_data

    def analyze_text(self, query_text: str, execution_time: float, rows_examined: int) -> Dict[str, Any]:
        suggestions: List[Dict[str, Any]] = []
        q = query_text.upper()
        if "JOIN" in q:
            suggestions.append({"type": "join_index", "description": "为 JOIN 列添加索引", "impact": "high"})
        if "LIKE '%" in query_text or "LIKE \"%" in query_text:
            suggestions.append({"type": "range_predicate", "description": "考虑前缀、分词或倒排索引", "impact": "medium"})
        return {
            "query_analysis": {"complexity_score": 55, "efficiency_score": 62, "performance_rating": "fair"},
            "suggestions": suggestions[:5],
            "priority_score": 70,
            "estimated_improvement": "40-70%",
        }

    def patterns(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        return {"total_slow_queries": 0, "avg_execution_time": 0.0, "most_common_patterns": [], "top_tables": []}

    def statistics(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        return {
            "period": f"{days}天",
            "total_queries": 0,
            "slow_queries": 0,
            "slow_query_percentage": 0.0,
            "avg_execution_time": 0.0,
            "max_execution_time": 0.0,
            "queries_per_second": 0.0,
            "trend": "stable",
        }


class _OBConfig:
    def __init__(self, session: Session):
        self._o = OceanBaseConfigOptimizer(session)

    def analyze_config(self, database_id: int) -> Dict[str, Any]:
        return self._o.analyze_configuration(database_id)

    def maintenance_strategy(self, database_id: int) -> Dict[str, Any]:
        return self._o.generate_maintenance_strategy(database_id)

    def optimize_memory(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        return self._o.optimize_memory_settings(system_info)

    def optimize_connections(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        return self._o.optimize_connection_settings(workload_info)

    def generate_tuning_script(self, analysis_results: Dict[str, Any]) -> str:
        return self._o.generate_performance_tuning_script(analysis_results)


class _OBExecutor:
    def __init__(self, session: Session):
        self._e = TuningExecutor(session)

    def execute_task(self, task_id: int) -> Dict[str, Any]:
        return self._e.execute_task(task_id)

    def stats(self, database_id: Optional[int] = None) -> Dict[str, Any]:
        return self._e.get_task_statistics(database_id)


class OceanBaseProvider:
    def __init__(self, session: Session):
        self.monitor = _OBMonitor(session)
        self.slow_queries = _OBSlowQueries(session)
        self.optimizer = _OBConfig(session)
        self.executor = _OBExecutor(session)

