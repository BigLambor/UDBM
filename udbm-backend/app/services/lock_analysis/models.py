"""
锁分析数据模型

定义所有核心数据结构
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class LockType(Enum):
    """锁类型枚举"""
    RELATION = "relation"
    TRANSACTION = "transaction"
    TUPLE = "tuple"
    PAGE = "page"
    ADVISORY = "advisory"
    ROW = "row"
    TABLE = "table"
    METADATA = "metadata"


class LockMode(Enum):
    """锁模式枚举"""
    # PostgreSQL锁模式
    ACCESS_SHARE = "AccessShareLock"
    ROW_SHARE = "RowShareLock"
    ROW_EXCLUSIVE = "RowExclusiveLock"
    SHARE_UPDATE_EXCLUSIVE = "ShareUpdateExclusiveLock"
    SHARE = "ShareLock"
    SHARE_ROW_EXCLUSIVE = "ShareRowExclusiveLock"
    EXCLUSIVE = "ExclusiveLock"
    ACCESS_EXCLUSIVE = "AccessExclusiveLock"
    
    # MySQL锁模式
    SHARED = "S"
    EXCLUSIVE = "X"
    INTENTION_SHARED = "IS"
    INTENTION_EXCLUSIVE = "IX"


@dataclass
class LockSnapshot:
    """锁快照数据模型"""
    lock_id: str
    lock_type: LockType
    lock_mode: LockMode
    database_id: int
    object_name: str
    session_id: str
    process_id: int
    granted: bool
    query_text: Optional[str] = None
    wait_start: Optional[datetime] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def wait_duration(self) -> Optional[float]:
        """计算等待时长（秒）"""
        if self.wait_start and not self.granted:
            return (datetime.now() - self.wait_start).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "lock_id": self.lock_id,
            "lock_type": self.lock_type.value,
            "lock_mode": self.lock_mode.value,
            "database_id": self.database_id,
            "object_name": self.object_name,
            "session_id": self.session_id,
            "process_id": self.process_id,
            "granted": self.granted,
            "query_text": self.query_text,
            "wait_duration": self.wait_duration,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class WaitChain:
    """锁等待链数据模型"""
    chain_id: str
    chain_length: int
    total_wait_time: float
    head_session_id: str  # 被阻塞的会话
    tail_session_id: str  # 阻塞源头
    nodes: List[Dict[str, Any]]  # 链上的所有节点
    is_cycle: bool = False  # 是否为环路（死锁）
    severity: str = "low"  # low, medium, high, critical
    
    def get_blocking_query(self) -> Optional[str]:
        """获取阻塞查询"""
        if self.nodes:
            return self.nodes[-1].get('query_text')
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chain_id": self.chain_id,
            "chain_length": self.chain_length,
            "total_wait_time": self.total_wait_time,
            "head_session_id": self.head_session_id,
            "tail_session_id": self.tail_session_id,
            "nodes": self.nodes,
            "is_cycle": self.is_cycle,
            "severity": self.severity,
            "blocking_query": self.get_blocking_query()
        }


@dataclass
class ContentionMetrics:
    """竞争指标数据模型"""
    object_name: str
    database_id: int
    contention_count: int
    total_wait_time: float
    avg_wait_time: float
    max_wait_time: float
    affected_sessions: int
    lock_mode_distribution: Dict[str, int]
    pattern: str = "normal"  # normal, hot_spot, burst, periodic
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "object_name": self.object_name,
            "database_id": self.database_id,
            "contention_count": self.contention_count,
            "total_wait_time": self.total_wait_time,
            "avg_wait_time": self.avg_wait_time,
            "max_wait_time": self.max_wait_time,
            "affected_sessions": self.affected_sessions,
            "lock_mode_distribution": self.lock_mode_distribution,
            "pattern": self.pattern,
            "confidence": self.confidence
        }


@dataclass
class LockStatistics:
    """锁统计信息"""
    database_id: int
    total_locks: int
    waiting_locks: int
    granted_locks: int
    deadlock_count: int
    timeout_count: int
    lock_type_distribution: Dict[str, int]
    collection_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "database_id": self.database_id,
            "total_locks": self.total_locks,
            "waiting_locks": self.waiting_locks,
            "granted_locks": self.granted_locks,
            "deadlock_count": self.deadlock_count,
            "timeout_count": self.timeout_count,
            "lock_type_distribution": self.lock_type_distribution,
            "collection_time": self.collection_time.isoformat()
        }


@dataclass
class AnalysisResult:
    """分析结果数据模型"""
    database_id: int
    health_score: float  # 0-100
    wait_chains: List[WaitChain]
    contentions: List[ContentionMetrics]
    statistics: LockStatistics
    recommendations: List['OptimizationAdvice']
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "database_id": self.database_id,
            "health_score": self.health_score,
            "wait_chains": [wc.to_dict() for wc in self.wait_chains],
            "contentions": [c.to_dict() for c in self.contentions],
            "statistics": self.statistics.to_dict(),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class OptimizationAdvice:
    """优化建议数据模型"""
    advice_id: str
    type: str  # index, query, isolation, config, schema
    priority: str  # critical, high, medium, low
    title: str
    description: str
    object_name: Optional[str]
    impact_score: float  # 预估影响分数 0-100
    sql_script: Optional[str]
    rollback_script: Optional[str]
    estimated_improvement: str
    actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "advice_id": self.advice_id,
            "type": self.type,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "object_name": self.object_name,
            "impact_score": self.impact_score,
            "sql_script": self.sql_script,
            "rollback_script": self.rollback_script,
            "estimated_improvement": self.estimated_improvement,
            "actions": self.actions
        }