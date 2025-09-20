"""
OceanBase 配置优化器
提供OceanBase租户级/集群级的配置分析、维护策略与调优脚本生成（Mock+规则）
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OceanBaseConfigOptimizer:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.use_real_data = False  # 首版默认使用Mock，后续可接入GV$视图

    def analyze_configuration(self, database_id: int) -> Dict[str, Any]:
        current = self._get_mock_ob_config()
        recommendations = self._generate_config_recommendations(current)
        score = self._calculate_score(current)
        return {
            "current_config": current,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "optimization_score": score,
            "data_source": "mock_data",
        }

    def generate_maintenance_strategy(self, database_id: int) -> Dict[str, Any]:
        return {
            "merge": {
                "major_compaction": {
                    "recommended_window": "02:00-06:00",
                    "concurrency": 4,
                    "priority": "medium",
                },
                "minor_compaction": {
                    "trigger_policy": "auto",
                    "pending_threshold": 20,
                },
            },
            "stats": {
                "gather_table_stats_daily": True,
                "skew_check": True,
            },
            "monitoring": [
                "监控计划缓存命中率(plan_cache_hit_ratio)",
                "监控RPC队列长度(rpc_queue_len)",
                "监控日志盘使用率(log_disk_usage_percent)",
            ],
        }

    def optimize_memory_settings(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        total_memory_gb = system_info.get("total_memory_gb", 32)
        tenant_memory = int(total_memory_gb * 0.6)
        memstore = max(1, int(tenant_memory * 0.2))
        return {
            "current_memory": f"{total_memory_gb}GB",
            "recommendations": {
                "tenant_memory_limit": f"{tenant_memory}G",
                "memstore_limit": f"{memstore}G",
                "plan_cache_mem_limit": f"{max(1, int(tenant_memory * 0.05))}G",
            },
            "rationale": {
                "tenant_memory_limit": "为租户分配合适内存，避免系统级回收",
                "memstore_limit": "保证写入与事务内存充足，避免写放大",
                "plan_cache_mem_limit": "保持计划缓存稳定命中率",
            },
        }

    def optimize_connection_settings(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        max_conn = workload_info.get("max_connections", 512)
        active = workload_info.get("active_connections", 120)
        return {
            "current_connections": active,
            "max_connections": max_conn,
            "recommendations": {
                "ob_tcp_invited_nodes": "配置允许接入的客户端IP段",
                "rpc_timeout": "3s",
                "ob_sql_audit_percent": 1,
            },
            "notes": "OceanBase连接由租户与Unit资源共同决定，应结合OBProxy与连接池设置",
        }

    def generate_performance_tuning_script(self, analysis_results: Dict[str, Any]) -> str:
        lines: List[str] = [
            "-- OceanBase Performance Tuning Script",
            f"-- Generated at: {datetime.now().isoformat()}",
            "-- 注意：以下命令部分需在租户层执行，且根据实际版本/权限调整",
            "",
        ]

        recs = analysis_results.get("recommendations", [])
        for rec in recs:
            param = rec.get("parameter")
            value = rec.get("recommended_value")
            if param and value is not None:
                lines.append(f"ALTER SYSTEM SET {param} = {value};")

        # 常用优化建议模板
        lines.extend([
            "",
            "-- 计划缓存与统计信息",
            "CALL DBMS_STATS.GATHER_DATABASE_STATS(); -- 若支持",
            "-- 固定热点SQL执行计划(示例 outline/hint)",
            "-- CREATE OUTLINE outline_fix_hot_sql ON SQL_ID='xxxx' HINT='/*+ leading(t) use_nl(j) */';",
            "",
            "-- 合并（Compaction）建议（在业务低峰执行）",
            "-- ALTER SYSTEM MAJOR FREEZE;",
            "-- ALTER SYSTEM MINOR FREEZE;",
        ])
        return "\n".join(lines)

    def _get_mock_ob_config(self) -> Dict[str, Any]:
        import random
        return {
            "tenant": {
                "name": "ob_tenant_demo",
                "unit_config": {
                    "cpu": random.choice([4, 8, 16]),
                    "memory_gb": random.choice([16, 32, 64]),
                    "log_disk_size_gb": random.choice([50, 100, 200]),
                },
            },
            "memory": {
                "tenant_memory_limit": "24G",
                "memstore_limit": "6G",
                "plan_cache_mem_limit": "2G",
            },
            "plan_cache": {
                "plan_cache_hit_ratio": round(random.uniform(88.0, 99.0), 2),
                "plan_cache_mem_used": f"{random.randint(512, 4096)}M",
            },
            "rpc": {
                "rpc_timeout": "3s",
                "rpc_queue_len": random.randint(0, 30),
            },
            "compaction": {
                "major_compaction_progress": round(random.uniform(70.0, 100.0), 1),
                "minor_compaction_pending": random.randint(0, 50),
            },
            "version": "OceanBase CE (mock)",
        }

    def _generate_config_recommendations(self, current: Dict[str, Any]) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []
        mem = current.get("memory", {})
        plan_cache = current.get("plan_cache", {})
        rpc = current.get("rpc", {})
        compaction = current.get("compaction", {})

        if mem.get("tenant_memory_limit") in ("16G", "24G"):
            recs.append({
                "category": "memory",
                "parameter": "tenant_memory_limit",
                "current_value": mem.get("tenant_memory_limit"),
                "recommended_value": "32G",
                "impact": "high",
                "description": "提升租户内存上限，降低回收压力",
            })

        if plan_cache.get("plan_cache_hit_ratio", 100) < 92:
            recs.append({
                "category": "plan_cache",
                "parameter": "plan_cache_mem_limit",
                "current_value": mem.get("plan_cache_mem_limit"),
                "recommended_value": "3G",
                "impact": "medium",
                "description": "增加计划缓存内存，提升命中率",
            })

        if rpc.get("rpc_queue_len", 0) > 15:
            recs.append({
                "category": "rpc",
                "parameter": "rpc_timeout",
                "current_value": rpc.get("rpc_timeout", "3s"),
                "recommended_value": "2s",
                "impact": "medium",
                "description": "缩短RPC超时，避免长队列堆积",
            })

        if compaction.get("major_compaction_progress", 100) < 85:
            recs.append({
                "category": "compaction",
                "parameter": "merge_concurrency",
                "current_value": 2,
                "recommended_value": 4,
                "impact": "medium",
                "description": "提升合并并发度，在低峰加速合并",
            })

        return recs

    def _calculate_score(self, current: Dict[str, Any]) -> float:
        score = 70.0
        if current.get("plan_cache", {}).get("plan_cache_hit_ratio", 100) >= 95:
            score += 10
        if current.get("rpc", {}).get("rpc_queue_len", 0) <= 10:
            score += 10
        return min(100.0, score)

