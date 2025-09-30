"""
MySQL锁数据采集器

实现MySQL数据库的真实锁数据采集
支持MySQL 5.7+ 和 MySQL 8.0+
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..interfaces import ILockDataCollector
from ..models import LockSnapshot, WaitChain, LockStatistics, LockType, LockMode
from ..factories import register_collector
from .base import BaseLockCollector, async_retry, measure_time

logger = logging.getLogger(__name__)


@register_collector('mysql')
class MySQLLockCollector(BaseLockCollector, ILockDataCollector):
    """
    MySQL锁数据采集器
    
    使用performance_schema和information_schema采集锁信息
    """
    
    # MySQL 8.0+ 锁查询SQL
    CURRENT_LOCKS_QUERY_MYSQL8 = """
    SELECT 
        l.ENGINE_TRANSACTION_ID as trx_id,
        l.ENGINE_LOCK_ID as lock_id,
        l.LOCK_TYPE as lock_type,
        l.LOCK_MODE as lock_mode,
        l.LOCK_STATUS as lock_status,
        l.LOCK_DATA as lock_data,
        l.OBJECT_SCHEMA as object_schema,
        l.OBJECT_NAME as object_name,
        l.INDEX_NAME as index_name,
        t.trx_id,
        t.trx_state,
        t.trx_started,
        t.trx_query,
        t.trx_mysql_thread_id as thread_id,
        TIMESTAMPDIFF(SECOND, t.trx_started, NOW()) as trx_duration
    FROM performance_schema.data_locks l
    LEFT JOIN information_schema.innodb_trx t 
        ON l.ENGINE_TRANSACTION_ID = t.trx_id
    WHERE t.trx_state != 'COMMITTED'
    ORDER BY t.trx_started;
    """
    
    # MySQL 5.7 锁查询SQL（降级方案）
    CURRENT_LOCKS_QUERY_MYSQL57 = """
    SELECT 
        t.trx_id,
        t.trx_state,
        t.trx_started,
        t.trx_query,
        t.trx_mysql_thread_id as thread_id,
        TIMESTAMPDIFF(SECOND, t.trx_started, NOW()) as trx_duration,
        l.lock_mode,
        l.lock_type,
        l.lock_table,
        l.lock_index,
        l.lock_data
    FROM information_schema.innodb_trx t
    LEFT JOIN information_schema.innodb_locks l ON t.trx_id = l.lock_trx_id
    WHERE t.trx_state != 'COMMITTED'
    ORDER BY t.trx_started;
    """
    
    # 锁等待查询SQL (MySQL 8.0+)
    LOCK_WAITS_QUERY_MYSQL8 = """
    SELECT 
        w.REQUESTING_ENGINE_TRANSACTION_ID as requesting_trx_id,
        w.REQUESTING_ENGINE_LOCK_ID as requesting_lock_id,
        w.REQUESTING_THREAD_ID as requesting_thread,
        w.BLOCKING_ENGINE_TRANSACTION_ID as blocking_trx_id,
        w.BLOCKING_ENGINE_LOCK_ID as blocking_lock_id,
        w.BLOCKING_THREAD_ID as blocking_thread,
        rt.trx_query as requesting_query,
        bt.trx_query as blocking_query,
        rt.trx_started as requesting_start,
        TIMESTAMPDIFF(SECOND, rt.trx_started, NOW()) as wait_time
    FROM performance_schema.data_lock_waits w
    JOIN information_schema.innodb_trx rt 
        ON w.REQUESTING_ENGINE_TRANSACTION_ID = rt.trx_id
    JOIN information_schema.innodb_trx bt 
        ON w.BLOCKING_ENGINE_TRANSACTION_ID = bt.trx_id
    ORDER BY wait_time DESC;
    """
    
    # 锁等待查询SQL (MySQL 5.7)
    LOCK_WAITS_QUERY_MYSQL57 = """
    SELECT 
        r.trx_id AS requesting_trx_id,
        r.trx_mysql_thread_id AS requesting_thread,
        r.trx_query AS requesting_query,
        b.trx_id AS blocking_trx_id,
        b.trx_mysql_thread_id AS blocking_thread,
        b.trx_query AS blocking_query,
        TIMESTAMPDIFF(SECOND, r.trx_wait_started, NOW()) AS wait_time
    FROM information_schema.innodb_lock_waits w
    JOIN information_schema.innodb_trx r ON w.requesting_trx_id = r.trx_id
    JOIN information_schema.innodb_trx b ON w.blocking_trx_id = b.trx_id
    ORDER BY wait_time DESC;
    """
    
    # 锁统计SQL
    LOCK_STATS_QUERY = """
    SELECT 
        COUNT(DISTINCT trx_id) as total_transactions,
        COUNT(*) FILTER (WHERE trx_state = 'LOCK WAIT') as waiting_transactions,
        SUM(CASE WHEN trx_state = 'LOCK WAIT' 
            THEN TIMESTAMPDIFF(SECOND, trx_wait_started, NOW()) 
            ELSE 0 END) as total_wait_time
    FROM information_schema.innodb_trx
    WHERE trx_state != 'COMMITTED';
    """
    
    def __init__(self, database_id: int, pool: Any):
        """
        初始化MySQL采集器
        
        Args:
            database_id: 数据库ID
            pool: aiomysql连接池
        """
        super().__init__(database_id, pool)
        self.mysql_version = None
        self.use_mysql8_queries = True  # 默认使用MySQL 8.0查询
    
    async def _detect_mysql_version(self) -> str:
        """检测MySQL版本"""
        if self.mysql_version:
            return self.mysql_version
        
        try:
            version = await self._execute_query_val("SELECT VERSION()")
            self.mysql_version = version
            
            # 判断是否为MySQL 8.0+
            if version and '8.' in str(version):
                self.use_mysql8_queries = True
                self.logger.info(f"Detected MySQL 8.x: {version}")
            else:
                self.use_mysql8_queries = False
                self.logger.info(f"Detected MySQL 5.x or MariaDB: {version}")
            
            return version
        except Exception as e:
            self.logger.error(f"Failed to detect MySQL version: {e}")
            self.use_mysql8_queries = False
            return "unknown"
    
    @async_retry(max_attempts=3, delay=1.0)
    @measure_time
    async def collect_current_locks(self) -> List[LockSnapshot]:
        """
        采集当前锁状态
        
        Returns:
            List[LockSnapshot]: 锁快照列表
        """
        try:
            # 检测MySQL版本
            await self._detect_mysql_version()
            
            # 选择合适的查询
            query = (self.CURRENT_LOCKS_QUERY_MYSQL8 
                    if self.use_mysql8_queries 
                    else self.CURRENT_LOCKS_QUERY_MYSQL57)
            
            rows = await self._execute_query(query)
            
            locks = []
            for row in rows:
                lock = self._parse_lock_row(row)
                if lock:
                    locks.append(lock)
            
            self.logger.info(f"Collected {len(locks)} locks from MySQL")
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
        lock_type_str = row.get('lock_type', 'RECORD')
        if lock_type_str == 'RECORD':
            lock_type = LockType.ROW
        elif lock_type_str == 'TABLE':
            lock_type = LockType.TABLE
        else:
            lock_type = LockType.RELATION
        
        # 解析锁模式
        lock_mode_str = row.get('lock_mode', 'X')
        try:
            if lock_mode_str in ['S', 'X', 'IS', 'IX']:
                lock_mode = LockMode(lock_mode_str)
            else:
                lock_mode = LockMode.EXCLUSIVE
        except:
            lock_mode = LockMode.EXCLUSIVE
        
        # 判断是否已授予
        granted = row.get('lock_status', 'GRANTED') == 'GRANTED'
        
        # 构建对象名称
        if self.use_mysql8_queries:
            object_name = f"{row.get('object_schema', 'unknown')}.{row.get('object_name', 'unknown')}"
        else:
            object_name = row.get('lock_table', 'unknown')
        
        # 构建锁快照
        lock = LockSnapshot(
            lock_id=str(row.get('lock_id', row.get('trx_id', 0))),
            lock_type=lock_type,
            lock_mode=lock_mode,
            database_id=self.database_id,
            object_name=object_name,
            session_id=str(row.get('thread_id', 0)),
            process_id=int(row.get('thread_id', 0)),
            granted=granted,
            query_text=row.get('trx_query'),
            wait_start=row.get('trx_started') if not granted else None,
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
            # 检测MySQL版本
            await self._detect_mysql_version()
            
            # 选择合适的查询
            query = (self.LOCK_WAITS_QUERY_MYSQL8 
                    if self.use_mysql8_queries 
                    else self.LOCK_WAITS_QUERY_MYSQL57)
            
            rows = await self._execute_query(query)
            
            # 构建等待链
            chains = []
            for i, row in enumerate(rows, 1):
                chain = WaitChain(
                    chain_id=f"mysql_chain_{i}",
                    chain_length=2,  # MySQL通常只显示直接的阻塞关系
                    total_wait_time=float(row.get('wait_time', 0)),
                    head_session_id=str(row.get('requesting_thread', 0)),
                    tail_session_id=str(row.get('blocking_thread', 0)),
                    is_cycle=False,  # MySQL InnoDB会自动检测和解决死锁
                    nodes=[
                        {
                            'thread_id': row.get('requesting_thread'),
                            'query_text': row.get('requesting_query'),
                            'level': 0,
                            'type': 'blocked'
                        },
                        {
                            'thread_id': row.get('blocking_thread'),
                            'query_text': row.get('blocking_query'),
                            'level': 1,
                            'type': 'blocking'
                        }
                    ],
                    severity=self._assess_severity_simple(float(row.get('wait_time', 0)))
                )
                chains.append(chain)
            
            self.logger.info(f"Collected {len(chains)} wait chains from MySQL")
            return chains
            
        except Exception as e:
            self.logger.error(f"Failed to collect wait chains: {e}", exc_info=True)
            return []
    
    def _assess_severity_simple(self, wait_time: float) -> str:
        """
        简单的严重程度评估
        
        Args:
            wait_time: 等待时间（秒）
            
        Returns:
            str: 严重程度
        """
        if wait_time >= 30:
            return "critical"
        elif wait_time >= 15:
            return "high"
        elif wait_time >= 5:
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
            # 查询InnoDB状态
            rows = await self._execute_query("SHOW ENGINE INNODB STATUS")
            innodb_status = rows[0]['Status'] if rows else ""
            
            # 从状态中提取死锁信息（简单解析）
            deadlock_count = innodb_status.count("LATEST DETECTED DEADLOCK") if innodb_status else 0
            
            # 查询当前锁统计
            total_locks = 0
            waiting_locks = 0
            
            try:
                # 尝试查询详细统计
                stat_row = await self._execute_query_one(
                    """
                    SELECT 
                        COUNT(*) as total_trx,
                        SUM(CASE WHEN trx_state = 'LOCK WAIT' THEN 1 ELSE 0 END) as waiting_trx
                    FROM information_schema.innodb_trx
                    WHERE trx_state != 'COMMITTED'
                    """
                )
                if stat_row:
                    total_locks = stat_row.get('total_trx', 0)
                    waiting_locks = stat_row.get('waiting_trx', 0)
            except Exception as e:
                self.logger.warning(f"Failed to query detailed lock stats: {e}")
            
            statistics = LockStatistics(
                database_id=self.database_id,
                total_locks=total_locks,
                waiting_locks=waiting_locks,
                granted_locks=total_locks - waiting_locks,
                deadlock_count=deadlock_count,
                timeout_count=0,  # MySQL不直接提供超时统计
                lock_type_distribution={},
                collection_time=datetime.now()
            )
            
            self.logger.info(f"Collected MySQL lock statistics: {total_locks} total, {waiting_locks} waiting")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to collect statistics: {e}", exc_info=True)
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