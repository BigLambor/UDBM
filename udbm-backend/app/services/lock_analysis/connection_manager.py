"""
连接池管理器

统一管理到目标数据库的连接池
"""
import logging
import asyncio
from typing import Dict, Optional, Any
import asyncpg
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """
    连接池管理器
    
    职责：
    1. 创建和管理到目标数据库的连接池
    2. 连接池复用和自动清理
    3. 健康检查和自动重连
    """
    
    _instance = None
    _pools: Dict[int, Any] = {}  # database_id -> pool
    _pool_info: Dict[int, Dict] = {}  # database_id -> connection info
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_pool(
        cls,
        database_id: int,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        min_size: int = 2,
        max_size: int = 10
    ) -> Optional[Any]:
        """
        获取或创建连接池
        
        Args:
            database_id: 数据库ID
            db_type: 数据库类型 (postgresql, mysql)
            host: 主机
            port: 端口
            database: 数据库名
            username: 用户名
            password: 密码
            min_size: 最小连接数
            max_size: 最大连接数
            
        Returns:
            连接池对象
        """
        # 检查是否已存在连接池
        if database_id in cls._pools:
            pool = cls._pools[database_id]
            
            # 检查连接池是否仍然有效
            try:
                if db_type.lower() == 'postgresql':
                    # PostgreSQL连接池健康检查
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                    logger.debug(f"Reusing existing pool for database {database_id}")
                    return pool
            except Exception as e:
                logger.warning(f"Existing pool unhealthy, recreating: {e}")
                await cls.close_pool(database_id)
        
        # 创建新连接池
        try:
            if db_type.lower() == 'postgresql':
                pool = await cls._create_postgresql_pool(
                    host, port, database, username, password,
                    min_size, max_size
                )
            elif db_type.lower() in ['mysql', 'oceanbase']:
                pool = await cls._create_mysql_pool(
                    host, port, database, username, password,
                    min_size, max_size
                )
            else:
                logger.error(f"Unsupported database type: {db_type}")
                return None
            
            # 保存连接池和信息
            cls._pools[database_id] = pool
            cls._pool_info[database_id] = {
                'db_type': db_type,
                'host': host,
                'port': port,
                'database': database,
                'created_at': datetime.now(),
                'min_size': min_size,
                'max_size': max_size
            }
            
            logger.info(
                f"Created connection pool for database {database_id} "
                f"({db_type} @ {host}:{port}/{database})"
            )
            
            return pool
            
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}", exc_info=True)
            return None
    
    @classmethod
    async def _create_postgresql_pool(
        cls,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        min_size: int,
        max_size: int
    ):
        """创建PostgreSQL连接池"""
        pool = await asyncpg.create_pool(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            min_size=min_size,
            max_size=max_size,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            timeout=30
        )
        return pool
    
    @classmethod
    async def _create_mysql_pool(
        cls,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        min_size: int,
        max_size: int
    ):
        """创建MySQL连接池"""
        try:
            import aiomysql
            
            pool = await aiomysql.create_pool(
                host=host,
                port=port,
                db=database,
                user=username,
                password=password,
                minsize=min_size,
                maxsize=max_size,
                autocommit=True,
                charset='utf8mb4'
            )
            return pool
        except ImportError:
            logger.error("aiomysql not installed. Run: pip install aiomysql")
            return None
    
    @classmethod
    async def close_pool(cls, database_id: int) -> bool:
        """
        关闭连接池
        
        Args:
            database_id: 数据库ID
            
        Returns:
            bool: 是否关闭成功
        """
        if database_id not in cls._pools:
            return False
        
        try:
            pool = cls._pools[database_id]
            
            # 关闭连接池
            if hasattr(pool, 'close'):
                await pool.close()
            elif hasattr(pool, 'wait_closed'):
                pool.close()
                await pool.wait_closed()
            
            # 移除记录
            del cls._pools[database_id]
            del cls._pool_info[database_id]
            
            logger.info(f"Closed connection pool for database {database_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to close pool: {e}", exc_info=True)
            return False
    
    @classmethod
    async def close_all_pools(cls):
        """关闭所有连接池"""
        database_ids = list(cls._pools.keys())
        
        for database_id in database_ids:
            await cls.close_pool(database_id)
        
        logger.info("All connection pools closed")
    
    @classmethod
    def get_pool_info(cls, database_id: int) -> Optional[Dict]:
        """
        获取连接池信息
        
        Args:
            database_id: 数据库ID
            
        Returns:
            连接池信息
        """
        return cls._pool_info.get(database_id)
    
    @classmethod
    def list_active_pools(cls) -> list:
        """
        列出所有活跃的连接池
        
        Returns:
            数据库ID列表
        """
        return list(cls._pools.keys())