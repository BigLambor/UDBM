"""
锁分析模块重构示例代码
展示重构后的核心代码结构和设计模式应用
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import asyncpg
import logging
from functools import wraps

logger = logging.getLogger(__name__)


# ============================================================================
# 1. 数据模型层 (Domain Models)
# ============================================================================

class LockType(Enum):
    """锁类型枚举"""
    RELATION = "relation"
    TRANSACTION = "transaction"
    TUPLE = "tuple"
    PAGE = "page"
    ADVISORY = "advisory"


class LockMode(Enum):
    """锁模式枚举"""
    ACCESS_SHARE = "AccessShareLock"
    ROW_SHARE = "RowShareLock"
    ROW_EXCLUSIVE = "RowExclusiveLock"
    SHARE = "ShareLock"
    EXCLUSIVE = "ExclusiveLock"


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


# ============================================================================
# 2. 接口定义层 (Interfaces)
# ============================================================================

class ILockDataCollector(ABC):
    """锁数据采集器接口"""
    
    @abstractmethod
    async def collect_current_locks(self) -> List[LockSnapshot]:
        """采集当前锁状态"""
        pass
    
    @abstractmethod
    async def collect_wait_chains(self) -> List[WaitChain]:
        """采集锁等待链"""
        pass
    
    @abstractmethod
    async def collect_statistics(self, duration: timedelta) -> LockStatistics:
        """采集锁统计信息"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class IAnalyzer(ABC):
    """分析器接口"""
    
    @abstractmethod
    async def analyze(self, data: Any) -> Any:
        """执行分析"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取分析器名称"""
        pass


class IOptimizationStrategy(ABC):
    """优化策略接口"""
    
    @abstractmethod
    def is_applicable(self, analysis: AnalysisResult) -> bool:
        """判断策略是否适用"""
        pass
    
    @abstractmethod
    async def generate(self, analysis: AnalysisResult) -> List[OptimizationAdvice]:
        """生成优化建议"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """获取策略优先级"""
        pass


# ============================================================================
# 3. 装饰器和工具函数
# ============================================================================

def async_retry(max_attempts: int = 3, delay: float = 1.0):
    """异步重试装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}"
                    )
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            
            logger.error(f"All {max_attempts} attempts failed")
            raise last_exception
        
        return wrapper
    return decorator


def measure_time(func: Callable):
    """性能测量装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper


# ============================================================================
# 4. PostgreSQL 数据采集器实现
# ============================================================================

class PostgreSQLLockCollector(ILockDataCollector):
    """PostgreSQL 锁数据采集器 - 真实数据采集"""
    
    def __init__(self, pool: asyncpg.Pool, database_id: int):
        self.pool = pool
        self.database_id = database_id
    
    @async_retry(max_attempts=3, delay=1.0)
    @measure_time
    async def collect_current_locks(self) -> List[LockSnapshot]:
        """采集当前锁状态"""
        query = """
        SELECT 
            l.locktype,
            l.database,
            l.relation,
            l.pid,
            l.mode,
            l.granted,
            a.query,
            a.query_start,
            c.relname as object_name,
            a.usename,
            a.application_name,
            a.client_addr,
            EXTRACT(EPOCH FROM (now() - a.query_start)) as query_duration
        FROM pg_locks l
        LEFT JOIN pg_stat_activity a ON l.pid = a.pid
        LEFT JOIN pg_class c ON l.relation = c.oid
        WHERE l.database = (SELECT oid FROM pg_database WHERE datname = current_database())
            AND (NOT l.granted OR l.locktype IN ('relation', 'transactionid'))
        ORDER BY a.query_start;
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            
            locks = []
            for row in rows:
                lock = LockSnapshot(
                    lock_id=f"{row['pid']}_{row['locktype']}_{row.get('relation', 0)}",
                    lock_type=LockType(row['locktype']) if row['locktype'] in [lt.value for lt in LockType] else LockType.RELATION,
                    lock_mode=LockMode(row['mode']) if row['mode'] in [lm.value for lm in LockMode] else LockMode.ACCESS_SHARE,
                    database_id=self.database_id,
                    object_name=row.get('object_name') or 'unknown',
                    session_id=str(row['pid']),
                    process_id=row['pid'],
                    granted=row['granted'],
                    query_text=row.get('query'),
                    wait_start=row.get('query_start') if not row['granted'] else None
                )
                locks.append(lock)
            
            logger.info(f"Collected {len(locks)} locks from PostgreSQL")
            return locks
    
    @async_retry(max_attempts=3, delay=1.0)
    @measure_time
    async def collect_wait_chains(self) -> List[WaitChain]:
        """采集锁等待链 - 使用递归CTE"""
        query = """
        WITH RECURSIVE blocking_tree AS (
            -- 基础查询：找到所有被阻塞的进程
            SELECT 
                blocked.pid AS blocked_pid,
                blocked.query AS blocked_query,
                blocking.pid AS blocking_pid,
                blocking.query AS blocking_query,
                1 AS level,
                ARRAY[blocked.pid] AS chain,
                blocked.query_start,
                EXTRACT(EPOCH FROM (now() - blocked.query_start)) as wait_time
            FROM pg_stat_activity AS blocked
            JOIN pg_locks AS blocked_locks ON blocked.pid = blocked_locks.pid
            JOIN pg_locks AS blocking_locks ON 
                blocked_locks.locktype = blocking_locks.locktype
                AND blocked_locks.database = blocking_locks.database
                AND (blocked_locks.relation = blocking_locks.relation OR blocked_locks.transactionid = blocking_locks.transactionid)
                AND blocked_locks.granted = false
                AND blocking_locks.granted = true
            JOIN pg_stat_activity AS blocking ON blocking_locks.pid = blocking.pid
            WHERE blocked.wait_event_type = 'Lock'
            
            UNION ALL
            
            -- 递归查询：继续追踪阻塞链
            SELECT 
                bt.blocked_pid,
                bt.blocked_query,
                next_blocking.pid,
                next_blocking.query,
                bt.level + 1,
                bt.chain || next_blocking.pid,
                bt.query_start,
                bt.wait_time
            FROM blocking_tree bt
            JOIN pg_stat_activity AS next_blocked ON bt.blocking_pid = next_blocked.pid
            JOIN pg_locks AS next_blocked_locks ON next_blocked.pid = next_blocked_locks.pid
            JOIN pg_locks AS next_blocking_locks ON 
                next_blocked_locks.locktype = next_blocking_locks.locktype
                AND next_blocked_locks.database = next_blocking_locks.database
                AND next_blocked_locks.granted = false
                AND next_blocking_locks.granted = true
            JOIN pg_stat_activity AS next_blocking ON next_blocking_locks.pid = next_blocking.pid
            WHERE next_blocked.wait_event_type = 'Lock'
                AND NOT next_blocking.pid = ANY(bt.chain)  -- 防止环路
                AND bt.level < 10  -- 限制递归深度
        )
        SELECT 
            blocked_pid,
            blocked_query,
            blocking_pid,
            blocking_query,
            level,
            chain,
            wait_time
        FROM blocking_tree
        ORDER BY level, wait_time DESC;
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            
            # 构建等待链
            chains_dict: Dict[str, WaitChain] = {}
            for row in rows:
                chain_key = f"chain_{row['blocked_pid']}"
                
                if chain_key not in chains_dict:
                    chains_dict[chain_key] = WaitChain(
                        chain_id=chain_key,
                        chain_length=row['level'],
                        total_wait_time=row['wait_time'] or 0.0,
                        head_session_id=str(row['blocked_pid']),
                        tail_session_id=str(row['blocking_pid']),
                        nodes=[
                            {
                                'pid': row['blocked_pid'],
                                'query_text': row['blocked_query'],
                                'level': 0
                            },
                            {
                                'pid': row['blocking_pid'],
                                'query_text': row['blocking_query'],
                                'level': row['level']
                            }
                        ]
                    )
            
            chains = list(chains_dict.values())
            
            # 评估严重程度
            for chain in chains:
                chain.severity = self._assess_severity(chain)
            
            logger.info(f"Collected {len(chains)} wait chains")
            return chains
    
    def _assess_severity(self, chain: WaitChain) -> str:
        """评估等待链严重程度"""
        if chain.is_cycle:
            return "critical"
        elif chain.chain_length >= 5 or chain.total_wait_time >= 30:
            return "critical"
        elif chain.chain_length >= 3 or chain.total_wait_time >= 15:
            return "high"
        elif chain.chain_length >= 2 or chain.total_wait_time >= 5:
            return "medium"
        else:
            return "low"
    
    @async_retry(max_attempts=3, delay=1.0)
    async def collect_statistics(self, duration: timedelta) -> LockStatistics:
        """采集锁统计信息"""
        async with self.pool.acquire() as conn:
            # 查询死锁信息
            deadlock_query = """
            SELECT deadlocks 
            FROM pg_stat_database 
            WHERE datname = current_database()
            """
            deadlocks = await conn.fetchval(deadlock_query)
            
            # 查询锁分布
            lock_dist_query = """
            SELECT 
                locktype,
                mode,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE NOT granted) as waiting_count
            FROM pg_locks
            WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
            GROUP BY locktype, mode
            """
            lock_dist_rows = await conn.fetch(lock_dist_query)
            
            lock_distribution = {}
            total_locks = 0
            waiting_locks = 0
            
            for row in lock_dist_rows:
                key = f"{row['locktype']}_{row['mode']}"
                lock_distribution[key] = row['count']
                total_locks += row['count']
                waiting_locks += row['waiting_count']
            
            return LockStatistics(
                database_id=self.database_id,
                total_locks=total_locks,
                waiting_locks=waiting_locks,
                granted_locks=total_locks - waiting_locks,
                deadlock_count=deadlocks or 0,
                timeout_count=0,  # PostgreSQL不直接提供超时统计
                lock_type_distribution=lock_distribution
            )
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# ============================================================================
# 5. 分析引擎实现
# ============================================================================

class WaitChainAnalyzer(IAnalyzer):
    """等待链分析器"""
    
    def get_name(self) -> str:
        return "WaitChainAnalyzer"
    
    async def analyze(self, chains: List[WaitChain]) -> Dict[str, Any]:
        """分析等待链"""
        if not chains:
            return {
                "total_chains": 0,
                "critical_chains": 0,
                "avg_chain_length": 0.0,
                "max_wait_time": 0.0,
                "has_deadlock": False
            }
        
        critical_chains = [c for c in chains if c.severity == "critical"]
        avg_length = sum(c.chain_length for c in chains) / len(chains)
        max_wait = max(c.total_wait_time for c in chains)
        has_deadlock = any(c.is_cycle for c in chains)
        
        return {
            "total_chains": len(chains),
            "critical_chains": len(critical_chains),
            "avg_chain_length": round(avg_length, 2),
            "max_wait_time": round(max_wait, 2),
            "has_deadlock": has_deadlock,
            "chains": chains
        }


class ContentionAnalyzer(IAnalyzer):
    """竞争分析器"""
    
    def get_name(self) -> str:
        return "ContentionAnalyzer"
    
    async def analyze(self, locks: List[LockSnapshot]) -> List[ContentionMetrics]:
        """分析锁竞争"""
        # 按对象分组统计
        contention_map: Dict[str, List[LockSnapshot]] = {}
        
        for lock in locks:
            if not lock.granted:  # 只统计未授予的锁（等待中）
                if lock.object_name not in contention_map:
                    contention_map[lock.object_name] = []
                contention_map[lock.object_name].append(lock)
        
        contentions = []
        for object_name, object_locks in contention_map.items():
            wait_times = [lock.wait_duration for lock in object_locks if lock.wait_duration]
            
            if not wait_times:
                continue
            
            # 统计锁模式分布
            mode_dist = {}
            for lock in object_locks:
                mode = lock.lock_mode.value
                mode_dist[mode] = mode_dist.get(mode, 0) + 1
            
            contention = ContentionMetrics(
                object_name=object_name,
                database_id=object_locks[0].database_id,
                contention_count=len(object_locks),
                total_wait_time=sum(wait_times),
                avg_wait_time=sum(wait_times) / len(wait_times),
                max_wait_time=max(wait_times),
                affected_sessions=len(set(lock.session_id for lock in object_locks)),
                lock_mode_distribution=mode_dist
            )
            
            # 识别竞争模式
            contention.pattern = self._identify_pattern(contention)
            
            contentions.append(contention)
        
        # 按总等待时间排序
        contentions.sort(key=lambda c: c.total_wait_time, reverse=True)
        
        return contentions
    
    def _identify_pattern(self, contention: ContentionMetrics) -> str:
        """识别竞争模式"""
        # 热点竞争：高频率 + 长等待时间
        if contention.contention_count > 10 and contention.avg_wait_time > 1.0:
            return "hot_spot"
        # 突发竞争：短时间内大量竞争
        elif contention.contention_count > 20:
            return "burst"
        else:
            return "normal"


class LockHealthScorer(IAnalyzer):
    """锁健康评分器"""
    
    WEIGHTS = {
        'wait_time': 0.30,
        'contention': 0.25,
        'deadlock': 0.20,
        'blocking_chain': 0.15,
        'timeout': 0.10
    }
    
    def get_name(self) -> str:
        return "LockHealthScorer"
    
    async def analyze(
        self, 
        chains: List[WaitChain],
        contentions: List[ContentionMetrics],
        statistics: LockStatistics
    ) -> float:
        """计算健康评分"""
        
        # 1. 等待时间评分
        if contentions:
            avg_wait = sum(c.avg_wait_time for c in contentions) / len(contentions)
            wait_score = self._score_wait_time(avg_wait)
        else:
            wait_score = 100.0
        
        # 2. 竞争评分
        contention_score = self._score_contention(contentions)
        
        # 3. 死锁评分
        deadlock_score = self._score_deadlock(statistics.deadlock_count)
        
        # 4. 阻塞链评分
        chain_score = self._score_blocking_chains(chains)
        
        # 5. 超时评分（如果有数据）
        timeout_score = 100.0  # 默认满分
        
        # 加权平均
        final_score = (
            wait_score * self.WEIGHTS['wait_time'] +
            contention_score * self.WEIGHTS['contention'] +
            deadlock_score * self.WEIGHTS['deadlock'] +
            chain_score * self.WEIGHTS['blocking_chain'] +
            timeout_score * self.WEIGHTS['timeout']
        )
        
        return max(0.0, min(100.0, round(final_score, 2)))
    
    def _score_wait_time(self, avg_wait: float) -> float:
        """等待时间评分"""
        if avg_wait < 0.1:
            return 95 + (0.1 - avg_wait) * 50
        elif avg_wait < 0.5:
            return 70 + (0.5 - avg_wait) / 0.4 * 25
        elif avg_wait < 2.0:
            return 50 + (2.0 - avg_wait) / 1.5 * 20
        elif avg_wait < 5.0:
            return 30 + (5.0 - avg_wait) / 3.0 * 20
        else:
            return max(0, 30 - (avg_wait - 5.0) * 5)
    
    def _score_contention(self, contentions: List[ContentionMetrics]) -> float:
        """竞争评分"""
        if not contentions:
            return 100.0
        
        hot_spots = sum(1 for c in contentions if c.pattern == "hot_spot")
        
        if hot_spots > 5:
            return 30.0
        elif hot_spots > 2:
            return 50.0
        elif hot_spots > 0:
            return 70.0
        else:
            return 90.0
    
    def _score_deadlock(self, deadlock_count: int) -> float:
        """死锁评分"""
        if deadlock_count == 0:
            return 100.0
        elif deadlock_count <= 2:
            return 80.0
        elif deadlock_count <= 5:
            return 60.0
        else:
            return 30.0
    
    def _score_blocking_chains(self, chains: List[WaitChain]) -> float:
        """阻塞链评分"""
        if not chains:
            return 100.0
        
        critical_chains = sum(1 for c in chains if c.severity == "critical")
        
        if critical_chains > 3:
            return 30.0
        elif critical_chains > 1:
            return 50.0
        elif critical_chains > 0:
            return 70.0
        else:
            return 90.0


# ============================================================================
# 6. 优化建议生成器
# ============================================================================

class IndexOptimizationStrategy(IOptimizationStrategy):
    """索引优化策略"""
    
    def is_applicable(self, analysis: AnalysisResult) -> bool:
        """判断是否适用"""
        # 如果存在热点竞争，可能需要索引优化
        hot_spots = [c for c in analysis.contentions if c.pattern == "hot_spot"]
        return len(hot_spots) > 0
    
    async def generate(self, analysis: AnalysisResult) -> List[OptimizationAdvice]:
        """生成索引优化建议"""
        advice_list = []
        
        hot_spots = [c for c in analysis.contentions if c.pattern == "hot_spot"]
        
        for contention in hot_spots[:3]:  # 只处理前3个热点
            advice = OptimizationAdvice(
                advice_id=f"idx_opt_{contention.object_name}",
                type="index",
                priority="high",
                title=f"为热点表 {contention.object_name} 优化索引",
                description=f"检测到表 {contention.object_name} 存在严重的锁竞争，"
                           f"竞争次数: {contention.contention_count}, "
                           f"平均等待时间: {contention.avg_wait_time:.2f}秒",
                object_name=contention.object_name,
                impact_score=self._calculate_impact(contention),
                sql_script=self._generate_index_sql(contention.object_name),
                rollback_script=f"DROP INDEX IF EXISTS idx_{contention.object_name}_optimization;",
                estimated_improvement="预计减少锁等待时间 30-50%",
                actions=[
                    "1. 分析热点表的查询模式",
                    "2. 识别缺失的索引",
                    "3. 在非高峰期创建索引",
                    "4. 监控索引效果"
                ]
            )
            advice_list.append(advice)
        
        return advice_list
    
    def get_priority(self) -> int:
        return 1  # 高优先级
    
    def _calculate_impact(self, contention: ContentionMetrics) -> float:
        """计算影响分数"""
        # 基于竞争次数和等待时间计算
        score = min(100, contention.contention_count * 2 + contention.total_wait_time)
        return round(score, 2)
    
    def _generate_index_sql(self, table_name: str) -> str:
        """生成索引SQL"""
        return f"""
-- 索引优化脚本
-- 目标表: {table_name}
-- 生成时间: {datetime.now().isoformat()}

-- 分析现有索引
SELECT 
    schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename = '{table_name}';

-- 建议创建复合索引（需要根据实际查询模式调整）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{table_name}_optimization
ON {table_name}(id, created_at)
WHERE deleted_at IS NULL;

-- 更新统计信息
ANALYZE {table_name};
"""


class QueryOptimizationStrategy(IOptimizationStrategy):
    """查询优化策略"""
    
    def is_applicable(self, analysis: AnalysisResult) -> bool:
        """判断是否适用"""
        # 如果存在长时间等待链，可能需要查询优化
        long_chains = [c for c in analysis.wait_chains if c.total_wait_time > 5.0]
        return len(long_chains) > 0
    
    async def generate(self, analysis: AnalysisResult) -> List[OptimizationAdvice]:
        """生成查询优化建议"""
        advice_list = []
        
        long_chains = [c for c in analysis.wait_chains if c.total_wait_time > 5.0]
        
        for chain in long_chains[:2]:
            blocking_query = chain.get_blocking_query()
            
            advice = OptimizationAdvice(
                advice_id=f"query_opt_{chain.chain_id}",
                type="query",
                priority="high" if chain.severity == "critical" else "medium",
                title=f"优化长时间阻塞查询",
                description=f"检测到查询导致长时间阻塞，等待时间: {chain.total_wait_time:.2f}秒",
                object_name=None,
                impact_score=min(100, chain.total_wait_time * 10),
                sql_script=None,
                rollback_script=None,
                estimated_improvement="预计减少阻塞时间 40-60%",
                actions=[
                    "1. 使用 EXPLAIN ANALYZE 分析查询执行计划",
                    "2. 检查是否缺少适当的索引",
                    "3. 考虑重写查询以减少锁持有时间",
                    "4. 使用更细粒度的锁（如行级锁代替表锁）",
                    f"5. 问题查询: {blocking_query[:100] if blocking_query else 'N/A'}"
                ]
            )
            advice_list.append(advice)
        
        return advice_list
    
    def get_priority(self) -> int:
        return 2  # 中高优先级


# ============================================================================
# 7. 分析编排器
# ============================================================================

class LockAnalysisOrchestrator:
    """锁分析编排器 - 协调所有分析组件"""
    
    def __init__(
        self,
        collector: ILockDataCollector,
        analyzers: List[IAnalyzer],
        strategies: List[IOptimizationStrategy]
    ):
        self.collector = collector
        self.analyzers = analyzers
        self.strategies = strategies
    
    @measure_time
    async def analyze_comprehensive(self, database_id: int) -> AnalysisResult:
        """执行综合分析"""
        
        # 1. 并行采集数据
        logger.info("Starting data collection...")
        locks, chains, statistics = await asyncio.gather(
            self.collector.collect_current_locks(),
            self.collector.collect_wait_chains(),
            self.collector.collect_statistics(timedelta(hours=1)),
            return_exceptions=True
        )
        
        # 处理异常
        if isinstance(locks, Exception):
            logger.error(f"Failed to collect locks: {locks}")
            locks = []
        if isinstance(chains, Exception):
            logger.error(f"Failed to collect chains: {chains}")
            chains = []
        if isinstance(statistics, Exception):
            logger.error(f"Failed to collect statistics: {statistics}")
            statistics = LockStatistics(
                database_id=database_id,
                total_locks=0,
                waiting_locks=0,
                granted_locks=0,
                deadlock_count=0,
                timeout_count=0,
                lock_type_distribution={}
            )
        
        # 2. 执行分析
        logger.info("Analyzing data...")
        
        # 分析竞争
        contention_analyzer = next(
            (a for a in self.analyzers if isinstance(a, ContentionAnalyzer)),
            ContentionAnalyzer()
        )
        contentions = await contention_analyzer.analyze(locks)
        
        # 计算健康评分
        health_scorer = next(
            (a for a in self.analyzers if isinstance(a, LockHealthScorer)),
            LockHealthScorer()
        )
        health_score = await health_scorer.analyze(chains, contentions, statistics)
        
        # 3. 生成优化建议
        logger.info("Generating optimization advice...")
        
        analysis_result = AnalysisResult(
            database_id=database_id,
            health_score=health_score,
            wait_chains=chains,
            contentions=contentions,
            statistics=statistics,
            recommendations=[]
        )
        
        all_advice = []
        for strategy in self.strategies:
            if strategy.is_applicable(analysis_result):
                advice = await strategy.generate(analysis_result)
                all_advice.extend(advice)
        
        # 按优先级和影响分数排序
        all_advice.sort(
            key=lambda a: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(a.priority, 3),
                -a.impact_score
            )
        )
        
        analysis_result.recommendations = all_advice
        
        logger.info(f"Analysis completed. Health score: {health_score:.2f}, "
                   f"Recommendations: {len(all_advice)}")
        
        return analysis_result


# ============================================================================
# 8. 使用示例
# ============================================================================

async def main():
    """主函数示例"""
    
    # 1. 创建连接池
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        database='testdb',
        user='postgres',
        password='password',
        min_size=5,
        max_size=10
    )
    
    try:
        # 2. 创建采集器
        collector = PostgreSQLLockCollector(pool=pool, database_id=1)
        
        # 3. 创建分析器
        analyzers = [
            WaitChainAnalyzer(),
            ContentionAnalyzer(),
            LockHealthScorer()
        ]
        
        # 4. 创建优化策略
        strategies = [
            IndexOptimizationStrategy(),
            QueryOptimizationStrategy()
        ]
        
        # 5. 创建编排器
        orchestrator = LockAnalysisOrchestrator(
            collector=collector,
            analyzers=analyzers,
            strategies=strategies
        )
        
        # 6. 执行分析
        result = await orchestrator.analyze_comprehensive(database_id=1)
        
        # 7. 打印结果
        print(f"\n{'='*60}")
        print(f"Lock Analysis Report - Database ID: {result.database_id}")
        print(f"{'='*60}")
        print(f"Health Score: {result.health_score:.2f}/100")
        print(f"Total Locks: {result.statistics.total_locks}")
        print(f"Waiting Locks: {result.statistics.waiting_locks}")
        print(f"Wait Chains: {len(result.wait_chains)}")
        print(f"Contentions: {len(result.contentions)}")
        print(f"Deadlocks: {result.statistics.deadlock_count}")
        
        print(f"\n{'='*60}")
        print(f"Top Contentions:")
        print(f"{'='*60}")
        for i, contention in enumerate(result.contentions[:5], 1):
            print(f"{i}. {contention.object_name}")
            print(f"   Count: {contention.contention_count}, "
                  f"Avg Wait: {contention.avg_wait_time:.3f}s, "
                  f"Pattern: {contention.pattern}")
        
        print(f"\n{'='*60}")
        print(f"Optimization Recommendations:")
        print(f"{'='*60}")
        for i, advice in enumerate(result.recommendations, 1):
            print(f"{i}. [{advice.priority.upper()}] {advice.title}")
            print(f"   Type: {advice.type}, Impact: {advice.impact_score:.1f}")
            print(f"   {advice.description}")
            print()
    
    finally:
        await pool.close()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行示例
    asyncio.run(main())