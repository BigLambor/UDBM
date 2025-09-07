"""
MySQL 配置优化器（初版，提供Mock/基础建议与脚本生成）
"""
from typing import Dict, Any, List
from datetime import datetime


class MySQLConfigOptimizer:
    """MySQL 配置优化器 - 提供配置分析、优化建议与脚本生成（SET PERSIST）"""

    def __init__(self, db_session):
        self.db = db_session

    def analyze_configuration(self, database_id: int) -> Dict[str, Any]:
        """
        返回当前配置与建议（当前以Mock为主，后续可通过 SHOW VARIABLES/STATUS 采集）
        """
        current = {
            "memory": {
                "innodb_buffer_pool_size": "1G",
                "tmp_table_size": "64M",
                "max_heap_table_size": "64M",
            },
            "connections": {
                "max_connections": 200,
                "thread_cache_size": 64,
                "table_open_cache": 4000,
            },
            "innodb": {
                "innodb_flush_log_at_trx_commit": 1,
                "innodb_log_file_size": "512M",
                "innodb_io_capacity": 2000,
            },
            "version": "MySQL 8.0.x (mock)"
        }

        recommendations = self._generate_config_recommendations(current)
        score = self._calculate_score(current)

        return {
            "current_config": current,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "optimization_score": score,
            "data_source": "mock_data"
        }

    def optimize_memory_settings(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        total_memory_gb = system_info.get("total_memory_gb", 8)
        buffer_pool = int(total_memory_gb * 0.5)  # 建议 40%-70% 之间
        return {
            "current_memory": f"{total_memory_gb}GB",
            "recommendations": {
                "innodb_buffer_pool_size": f"{buffer_pool}G",
                "tmp_table_size": "128M",
                "max_heap_table_size": "128M",
            },
            "rationale": {
                "innodb_buffer_pool_size": "提高InnoDB缓存命中率，减少磁盘IO",
                "tmp_table_size": "降低临时表落盘概率",
            }
        }

    def optimize_connection_settings(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        max_conn = workload_info.get("max_connections", 300)
        active = workload_info.get("active_connections", 80)
        return {
            "current_connections": active,
            "max_connections": max_conn,
            "recommendations": {
                "max_connections": min(max_conn, 500),
                "thread_cache_size": 128,
                "table_open_cache": 8192,
            }
        }

    def maintenance_strategy(self, database_id: int) -> Dict[str, Any]:
        return {
            "optimize_tables": [
                {"table": "orders", "action": "OPTIMIZE TABLE", "impact": "medium"},
                {"table": "users", "action": "ANALYZE TABLE", "impact": "low"},
            ],
            "monitoring": [
                "开启performance_schema并定期汇总digest",
                "监控临时表落盘与filesort",
            ]
        }

    def generate_performance_tuning_script(self, analysis_results: Dict[str, Any]) -> str:
        lines: List[str] = [
            "# MySQL Performance Tuning Script",
            f"# Generated at: {datetime.now().isoformat()}",
            "",
        ]

        # 从优化建议生成 SET PERSIST 语句
        recs = analysis_results.get("recommendations", [])
        for rec in recs:
            param = rec.get("parameter")
            value = rec.get("recommended_value")
            if param and value is not None:
                if isinstance(value, (int, float)):
                    lines.append(f"SET PERSIST {param} = {value};")
                else:
                    lines.append(f"SET PERSIST {param} = '{value}';")

        lines.extend([
            "",
            "-- TABLE MAINTENANCE",
            "ANALYZE TABLE users;",
            "OPTIMIZE TABLE orders;",
        ])

        return "\n".join(lines)

    def _generate_config_recommendations(self, current: Dict[str, Any]) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []
        mem = current.get("memory", {})
        innodb = current.get("innodb", {})

        if mem.get("innodb_buffer_pool_size") in ("1G", "2G"):
            recs.append({
                "category": "memory",
                "parameter": "innodb_buffer_pool_size",
                "current_value": mem.get("innodb_buffer_pool_size"),
                "recommended_value": "4G",
                "impact": "high",
                "description": "提高缓冲池减少物理IO"
            })

        if innodb.get("innodb_flush_log_at_trx_commit") == 1:
            recs.append({
                "category": "innodb",
                "parameter": "innodb_flush_log_at_trx_commit",
                "current_value": 1,
                "recommended_value": 2,
                "impact": "medium",
                "description": "在允许的持久性前提下降低fsync频率"
            })

        return recs

    def _calculate_score(self, current: Dict[str, Any]) -> float:
        score = 70.0
        mem = current.get("memory", {})
        if mem.get("innodb_buffer_pool_size") not in ("512M", "1G"):
            score += 10
        return min(100.0, score)

