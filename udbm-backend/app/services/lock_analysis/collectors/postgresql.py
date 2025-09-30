"""
PostgreSQL锁数据采集器

实现PostgreSQL数据库的真实锁数据采集
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..interfaces import ILockDataCollector
from ..models import LockSnapshot, WaitChain, LockStatistics, LockType, LockMode
from ..factories import register_collector
from .base import BaseLockCollector, async_retry, measure_time

logger = logging.getLogger(__name__)


@register_collector('postgresql')
class PostgreSQLLockCollector(BaseLockCollector, ILockDataCollector):
    """
    PostgreSQL锁数据采集器
    
    使用pg_locks和pg_stat_activity系统视图采集锁信息
    """
    
    # PostgreSQL锁查询SQL
    CURRENT_LOCKS_QUERY = """
    SELECT 
        l.locktype,
        l.database,
        l.relation,
        l.pid,
        l.mode,
        l.granted,
        a.query,
        a.query_start,
        a.state,
        a.wait_event_type,
        a.wait_event,
        COALESCE(c.relname, 'N/A') as object_name,
        a.usename,
        a.application_name,
        a.client_addr,
        EXTRACT(EPOCH FROM (now() - a.query_start)) as query_duration
    FROM pg_locks l
    LEFT JOIN pg_stat_activity a ON l.pid = a.pid
    LEFT JOIN pg_class c ON l.relation = c.oid
    WHERE l.database = (SELECT oid FROM pg_database WHERE datname = current_database())
        AND (NOT l.granted OR l.locktype IN ('relation', 'transactionid', 'tuple'))
        AND a.pid IS NOT NULL
    ORDER BY a.query_start;
    """
    
    WAIT_CHAINS_QUERY = """
    WITH RECURSIVE blocking_tree AS (
        -- 基础查询：找到所有被阻塞的进程
        SELECT 
            blocked.pid AS blocked_pid,
            blocked.query AS blocked_query,
            blocking.pid AS blocking_pid,
            blocking.query AS blocking_query,
            blocked.query_start AS blocked_start,
            1 AS level,
            ARRAY[blocked.pid] AS chain,
            EXTRACT(EPOCH FROM (now() - blocked.query_start)) as wait_time
        FROM pg_stat_activity AS blocked
        JOIN pg_locks AS blocked_locks ON blocked.pid = blocked_locks.pid
        JOIN pg_locks AS blocking_locks ON 
            blocked_locks.locktype = blocking_locks.locktype
            AND blocked_locks.database = blocking_locks.database
            AND (
                blocked_locks.relation = blocking_locks.relation 
                OR blocked_locks.transactionid = blocking_locks.transactionid
            )
            AND blocked_locks.granted = false
            AND blocking_locks.granted = true
        JOIN pg_stat_activity AS blocking ON blocking_locks.pid = blocking.pid
        WHERE blocked.wait_event_type = 'Lock'
            AND blocked.pid != blocking.pid
        
        UNION ALL
        
        -- 递归查询：继续追踪阻塞链
        SELECT 
            bt.blocked_pid,
            bt.blocked_query,
            next_blocking.pid,
            next_blocking.query,
            bt.blocked_start,
            bt.level + 1,
            bt.chain || next_blocking.pid,
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
            AND next_blocked.pid != next_blocking.pid
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
    
    DEADLOCK_QUERY = """
    SELECT deadlocks 
    FROM pg_stat_database 
    WHERE datname = current_database();
    """
    
    LOCK_DISTRIBUTION_QUERY = """
    SELECT 
        locktype,
        mode,
        COUNT(*) as count,
        COUNT(*) FILTER (WHERE NOT granted) as waiting_count
    FROM pg_locks
    WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
    GROUP BY locktype, mode;
    """
    
    @async_retry(max_attempts=3, delay=1.0)
    @measure_time
    async def collect_current_locks(self) -> List[LockSnapshot]:
        """
        采集当前锁状态
        
        Returns:
            List[LockSnapshot]: 锁快照列表
        """
        try:
            rows = await self._execute_query(self.CURRENT_LOCKS_QUERY)
            
            locks = []
            for row in rows:
                lock = self._parse_lock_row(row)
                if lock:
                    locks.append(lock)
            
            self.logger.info(f"Collected {len(locks)} locks from PostgreSQL")
            return locks
            
        except Exception as e:
            self.logger.error(f"Failed to collect current locks: {e}", exc_info=True)
            return []
    
    def _parse_lock_row(self, row: Any) -> LockSnapshot:
        """
        解析锁查询结果行
        
        Args:
            row: 查询结果行
            
        Returns:
            LockSnapshot: 锁快照对象
        """
        # 解析锁类型
        locktype = row['locktype']
        try:
            lock_type = LockType(locktype) if locktype in [lt.value for lt in LockType] else LockType.RELATION
        except:
            lock_type = LockType.RELATION
        
        # 解析锁模式
        mode = row['mode']
        try:
            lock_mode = LockMode(mode) if mode in [lm.value for lm in LockMode] else LockMode.ACCESS_SHARE
        except:
            lock_mode = LockMode.ACCESS_SHARE
        
        # 构建锁快照
        lock = LockSnapshot(
            lock_id=f"{row['pid']}_{row['locktype']}_{row.get('relation', 0)}",
            lock_type=lock_type,
            lock_mode=lock_mode,
            database_id=self.database_id,
            object_name=row.get('object_name') or 'N/A',
            session_id=str(row['pid']),
            process_id=row['pid'],
            granted=row['granted'],
            query_text=row.get('query'),
            wait_start=row.get('query_start') if not row['granted'] else None,
            timestamp=datetime.now()
        )
        
        return lock
    
    @async_retry(max_attempts=3, delay=1.0)
    @measure_time
    async def collect_wait_chains(self) -> List[WaitChain]:
        """
        采集锁等待链
        
        Returns:
            List[WaitChain]: 等待链列表
        """
        try:
            rows = await self._execute_query(self.WAIT_CHAINS_QUERY)
            
            # 构建等待链
            chains_dict: Dict[str, WaitChain] = {}
            
            for row in rows:
                chain_key = f"chain_{row['blocked_pid']}"
                
                if chain_key not in chains_dict:
                    # 检查是否为环路（死锁）
                    chain = list(row['chain'])
                    is_cycle = len(chain) != len(set(chain))
                    
                    chains_dict[chain_key] = WaitChain(
                        chain_id=chain_key,
                        chain_length=row['level'],
                        total_wait_time=row['wait_time'] or 0.0,
                        head_session_id=str(row['blocked_pid']),
                        tail_session_id=str(row['blocking_pid']),
                        is_cycle=is_cycle,
                        nodes=[
                            {
                                'pid': row['blocked_pid'],
                                'query_text': row['blocked_query'],
                                'level': 0,
                                'type': 'blocked'
                            },
                            {
                                'pid': row['blocking_pid'],
                                'query_text': row['blocking_query'],
                                'level': row['level'],
                                'type': 'blocking'
                            }
                        ]
                    )
            
            chains = list(chains_dict.values())
            
            # 评估严重程度
            for chain in chains:
                chain.severity = self._assess_severity(chain)
            
            self.logger.info(f"Collected {len(chains)} wait chains")
            return chains
            
        except Exception as e:
            self.logger.error(f"Failed to collect wait chains: {e}", exc_info=True)
            return []
    
    def _assess_severity(self, chain: WaitChain) -> str:
        """
        评估等待链严重程度
        
        Args:
            chain: 等待链
            
        Returns:
            str: 严重程度 (low, medium, high, critical)
        """
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
        """
        采集锁统计信息
        
        Args:
            duration: 统计时间范围
            
        Returns:
            LockStatistics: 锁统计数据
        """
        try:
            # 查询死锁信息
            deadlocks = await self._execute_query_val(self.DEADLOCK_QUERY) or 0
            
            # 查询锁分布
            lock_dist_rows = await self._execute_query(self.LOCK_DISTRIBUTION_QUERY)
            
            lock_distribution = {}
            total_locks = 0
            waiting_locks = 0
            
            for row in lock_dist_rows:
                key = f"{row['locktype']}_{row['mode']}"
                lock_distribution[key] = row['count']
                total_locks += row['count']
                waiting_locks += row['waiting_count']
            
            statistics = LockStatistics(
                database_id=self.database_id,
                total_locks=total_locks,
                waiting_locks=waiting_locks,
                granted_locks=total_locks - waiting_locks,
                deadlock_count=deadlocks,
                timeout_count=0,  # PostgreSQL不直接提供超时统计
                lock_type_distribution=lock_distribution,
                collection_time=datetime.now()
            )
            
            self.logger.info(f"Collected lock statistics: {total_locks} total, {waiting_locks} waiting")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to collect statistics: {e}", exc_info=True)
            # 返回空统计数据
            return LockStatistics(
                database_id=self.database_id,
                total_locks=0,
                waiting_locks=0,
                granted_locks=0,
                deadlock_count=0,
                timeout_count=0,
                lock_type_distribution={},
                collection_time=datetime.now()
            )
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 采集器是否正常工作
        """
        try:
            result = await self._execute_query_val("SELECT 1")
            return result == 1
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False