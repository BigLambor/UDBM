"""
基础采集器

提供通用的采集器功能和工具方法
"""
import logging
from typing import Any, Optional
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    异步重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避系数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} failed: {e}"
                    )
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"{func.__name__} failed after {max_attempts} attempts")
            raise last_exception
        
        return wrapper
    return decorator


def measure_time(func):
    """
    性能测量装饰器
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper


class BaseLockCollector:
    """
    基础采集器类
    
    提供通用功能和辅助方法
    """
    
    def __init__(self, database_id: int, pool: Any):
        """
        初始化采集器
        
        Args:
            database_id: 数据库ID
            pool: 连接池
        """
        self.database_id = database_id
        self.pool = pool
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{database_id}]")
    
    async def _execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """
        执行查询（带重试）
        
        Args:
            query: SQL查询
            params: 查询参数
            
        Returns:
            list: 查询结果
        """
        async with self.pool.acquire() as conn:
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
            return rows
    
    async def _execute_query_one(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        """
        执行查询并返回单行结果
        
        Args:
            query: SQL查询
            params: 查询参数
            
        Returns:
            Optional[Any]: 查询结果，无结果返回None
        """
        async with self.pool.acquire() as conn:
            if params:
                row = await conn.fetchrow(query, *params)
            else:
                row = await conn.fetchrow(query)
            return row
    
    async def _execute_query_val(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        """
        执行查询并返回单个值
        
        Args:
            query: SQL查询
            params: 查询参数
            
        Returns:
            Optional[Any]: 查询结果值
        """
        async with self.pool.acquire() as conn:
            if params:
                val = await conn.fetchval(query, *params)
            else:
                val = await conn.fetchval(query)
            return val