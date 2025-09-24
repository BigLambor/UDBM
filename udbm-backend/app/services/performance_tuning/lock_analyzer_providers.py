"""
不同数据库类型的锁分析实现
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random


class PostgreSQLLockAnalyzer:
    """PostgreSQL锁分析器"""
    
    @staticmethod
    def get_mock_data(database_id: int) -> Dict[str, Any]:
        """获取PostgreSQL模拟锁数据"""
        return {
            "database_type": "postgresql",
            "overall_health_score": 85 + random.randint(-10, 10),
            "lock_efficiency_score": 82 + random.randint(-10, 10),
            "contention_severity": random.choice(["low", "medium"]),
            "current_locks": 15 + random.randint(-5, 10),
            "waiting_locks": 2 + random.randint(0, 3),
            "deadlock_count_today": random.randint(0, 2),
            "timeout_count_today": random.randint(0, 5),
            "hot_objects": [
                {
                    "object_name": "public.users",
                    "contention_count": 25,
                    "total_wait_time": 12.5,
                    "avg_wait_time": 0.5,
                    "priority_level": "medium",
                    "lock_type": "RowExclusiveLock"
                },
                {
                    "object_name": "public.orders",
                    "contention_count": 18,
                    "total_wait_time": 8.3,
                    "avg_wait_time": 0.46,
                    "priority_level": "low",
                    "lock_type": "AccessShareLock"
                },
                {
                    "object_name": "public.products",
                    "contention_count": 12,
                    "total_wait_time": 5.2,
                    "avg_wait_time": 0.43,
                    "priority_level": "low",
                    "lock_type": "ShareLock"
                }
            ],
            "active_wait_chains": [
                {
                    "chain_id": f"pg_chain_{i}",
                    "chain_length": random.randint(2, 4),
                    "total_wait_time": round(random.uniform(1, 10), 2),
                    "severity_level": random.choice(["low", "medium", "high"]),
                    "head_session_id": f"pg_session_{random.randint(1000, 9999)}",
                    "tail_session_id": f"pg_session_{random.randint(1000, 9999)}",
                    "blocked_query": "UPDATE users SET last_login = NOW() WHERE id = ?",
                    "blocking_query": "SELECT * FROM users FOR UPDATE"
                }
                for i in range(random.randint(0, 2))
            ],
            "top_contentions": [],
            "optimization_suggestions": [
                {
                    "title": "优化长事务",
                    "description": "检测到多个长时间运行的事务，建议优化查询或拆分事务",
                    "priority": "high",
                    "actions": [
                        "检查并优化慢查询",
                        "考虑使用批处理减少锁持有时间",
                        "设置合理的statement_timeout"
                    ]
                },
                {
                    "title": "调整锁等待超时",
                    "description": "当前lock_timeout设置可能过长，建议调整",
                    "priority": "medium",
                    "actions": [
                        "设置lock_timeout = '10s'",
                        "配置deadlock_timeout = '1s'"
                    ]
                }
            ],
            "lock_trends": {
                "wait_time": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), 
                     "value": round(5.0 - i * 0.2 + random.uniform(-1, 1), 2)}
                    for i in range(24, 0, -1)
                ],
                "contention_count": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), 
                     "value": 10 + random.randint(-3, 5)}
                    for i in range(24, 0, -1)
                ]
            },
            "pg_specific_metrics": {
                "advisory_locks": random.randint(0, 5),
                "relation_locks": random.randint(10, 30),
                "transaction_locks": random.randint(5, 15),
                "vacuum_running": random.choice([True, False]),
                "autovacuum_workers": random.randint(0, 3)
            }
        }


class MySQLLockAnalyzer:
    """MySQL锁分析器"""
    
    @staticmethod
    def get_mock_data(database_id: int) -> Dict[str, Any]:
        """获取MySQL模拟锁数据"""
        return {
            "database_type": "mysql",
            "overall_health_score": 78 + random.randint(-10, 10),
            "lock_efficiency_score": 75 + random.randint(-10, 10),
            "contention_severity": random.choice(["low", "medium", "high"]),
            "current_locks": 20 + random.randint(-5, 15),
            "waiting_locks": 3 + random.randint(0, 5),
            "deadlock_count_today": random.randint(0, 3),
            "timeout_count_today": random.randint(0, 8),
            "hot_objects": [
                {
                    "object_name": "db.user_sessions",
                    "contention_count": 35,
                    "total_wait_time": 18.5,
                    "avg_wait_time": 0.53,
                    "priority_level": "high",
                    "lock_type": "RECORD LOCK"
                },
                {
                    "object_name": "db.transactions",
                    "contention_count": 28,
                    "total_wait_time": 14.2,
                    "avg_wait_time": 0.51,
                    "priority_level": "medium",
                    "lock_type": "TABLE LOCK"
                },
                {
                    "object_name": "db.inventory",
                    "contention_count": 22,
                    "total_wait_time": 10.8,
                    "avg_wait_time": 0.49,
                    "priority_level": "medium",
                    "lock_type": "GAP LOCK"
                }
            ],
            "active_wait_chains": [
                {
                    "chain_id": f"mysql_chain_{i}",
                    "chain_length": random.randint(2, 5),
                    "total_wait_time": round(random.uniform(2, 15), 2),
                    "severity_level": random.choice(["medium", "high"]),
                    "head_session_id": f"mysql_thread_{random.randint(1000, 9999)}",
                    "tail_session_id": f"mysql_thread_{random.randint(1000, 9999)}",
                    "blocked_query": "INSERT INTO transactions (user_id, amount) VALUES (?, ?)",
                    "blocking_query": "SELECT * FROM transactions WHERE user_id = ? FOR UPDATE",
                    "lock_mode": random.choice(["X", "S", "IX", "IS"])
                }
                for i in range(random.randint(1, 3))
            ],
            "top_contentions": [],
            "optimization_suggestions": [
                {
                    "title": "优化InnoDB行锁",
                    "description": "检测到频繁的行锁竞争，建议优化索引和查询",
                    "priority": "high",
                    "actions": [
                        "确保查询使用合适的索引",
                        "避免大范围的FOR UPDATE锁定",
                        "考虑使用READ COMMITTED隔离级别"
                    ]
                },
                {
                    "title": "调整InnoDB锁等待超时",
                    "description": "当前innodb_lock_wait_timeout可能需要调整",
                    "priority": "medium",
                    "actions": [
                        "设置innodb_lock_wait_timeout = 50",
                        "监控lock wait timeout exceeded错误"
                    ]
                },
                {
                    "title": "优化间隙锁使用",
                    "description": "检测到间隙锁导致的并发问题",
                    "priority": "medium",
                    "actions": [
                        "考虑使用READ COMMITTED隔离级别减少间隙锁",
                        "优化范围查询条件"
                    ]
                }
            ],
            "lock_trends": {
                "wait_time": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), 
                     "value": round(6.0 - i * 0.25 + random.uniform(-1.5, 1.5), 2)}
                    for i in range(24, 0, -1)
                ],
                "contention_count": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), 
                     "value": 15 + random.randint(-5, 8)}
                    for i in range(24, 0, -1)
                ]
            },
            "mysql_specific_metrics": {
                "innodb_row_locks": random.randint(15, 40),
                "innodb_table_locks": random.randint(2, 10),
                "metadata_locks": random.randint(0, 5),
                "gap_locks": random.randint(3, 15),
                "next_key_locks": random.randint(5, 20),
                "auto_inc_locks": random.randint(0, 3)
            }
        }


class OceanBaseLockAnalyzer:
    """OceanBase锁分析器"""
    
    @staticmethod
    def get_mock_data(database_id: int) -> Dict[str, Any]:
        """获取OceanBase模拟锁数据"""
        return {
            "database_type": "oceanbase",
            "overall_health_score": 88 + random.randint(-8, 8),
            "lock_efficiency_score": 85 + random.randint(-8, 8),
            "contention_severity": random.choice(["low", "low", "medium"]),
            "current_locks": 12 + random.randint(-3, 8),
            "waiting_locks": 1 + random.randint(0, 2),
            "deadlock_count_today": random.randint(0, 1),
            "timeout_count_today": random.randint(0, 3),
            "hot_objects": [
                {
                    "object_name": "tenant1.orders",
                    "contention_count": 15,
                    "total_wait_time": 6.5,
                    "avg_wait_time": 0.43,
                    "priority_level": "low",
                    "lock_type": "ROW_SHARE",
                    "tenant_name": "tenant1"
                },
                {
                    "object_name": "tenant1.user_balance",
                    "contention_count": 12,
                    "total_wait_time": 5.2,
                    "avg_wait_time": 0.43,
                    "priority_level": "low",
                    "lock_type": "ROW_EXCLUSIVE",
                    "tenant_name": "tenant1"
                }
            ],
            "active_wait_chains": [
                {
                    "chain_id": f"ob_chain_{i}",
                    "chain_length": random.randint(2, 3),
                    "total_wait_time": round(random.uniform(0.5, 5), 2),
                    "severity_level": "low",
                    "head_session_id": f"ob_session_{random.randint(1000, 9999)}",
                    "tail_session_id": f"ob_session_{random.randint(1000, 9999)}",
                    "tenant_id": random.randint(1000, 1003),
                    "blocked_query": "UPDATE orders SET status = ? WHERE order_id = ?",
                    "blocking_query": "SELECT * FROM orders WHERE user_id = ?"
                }
                for i in range(random.randint(0, 1))
            ],
            "top_contentions": [],
            "optimization_suggestions": [
                {
                    "title": "优化分布式事务",
                    "description": "检测到跨分区事务，建议优化数据分布",
                    "priority": "medium",
                    "actions": [
                        "检查表分区策略",
                        "优化事务边界，减少跨分区操作",
                        "考虑调整分区键"
                    ]
                },
                {
                    "title": "租户资源优化",
                    "description": "部分租户锁资源使用较高",
                    "priority": "low",
                    "actions": [
                        "检查租户资源配置",
                        "监控租户级别的锁统计"
                    ]
                }
            ],
            "lock_trends": {
                "wait_time": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), 
                     "value": round(3.0 - i * 0.1 + random.uniform(-0.5, 0.5), 2)}
                    for i in range(24, 0, -1)
                ],
                "contention_count": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), 
                     "value": 8 + random.randint(-2, 3)}
                    for i in range(24, 0, -1)
                ]
            },
            "oceanbase_specific_metrics": {
                "distributed_locks": random.randint(2, 8),
                "local_locks": random.randint(8, 20),
                "tenant_locks": {
                    "tenant1": random.randint(5, 15),
                    "tenant2": random.randint(3, 10),
                    "system": random.randint(1, 5)
                },
                "partition_locks": random.randint(3, 12),
                "global_index_locks": random.randint(0, 5)
            }
        }


class UnsupportedDatabaseLockAnalyzer:
    """不支持的数据库类型"""
    
    @staticmethod
    def get_mock_data(database_id: int) -> Dict[str, Any]:
        """返回不支持的提示"""
        return {
            "error": "unsupported",
            "message": "该数据库类型暂不支持锁分析功能"
        }


def get_lock_analyzer_by_type(db_type: str):
    """根据数据库类型获取对应的锁分析器"""
    analyzers = {
        "postgresql": PostgreSQLLockAnalyzer,
        "mysql": MySQLLockAnalyzer,
        "oceanbase": OceanBaseLockAnalyzer
    }
    
    return analyzers.get(db_type.lower(), UnsupportedDatabaseLockAnalyzer)