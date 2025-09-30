"""
缓存管理模块

实现多级缓存策略：
1. 本地内存缓存（L1）
2. Redis分布式缓存（L2）
"""
import pickle
import logging
from typing import Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LocalCache:
    """
    本地内存缓存（L1）
    
    使用字典实现简单的TTL缓存
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        """
        初始化本地缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict = {}
        self._expiry: dict = {}
        self._access_count: dict = {}
        
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，不存在或已过期返回None
        """
        # 检查是否存在
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._expiry and datetime.now() > self._expiry[key]:
            self._remove(key)
            return None
        
        # 更新访问计数
        self._access_count[key] = self._access_count.get(key, 0) + 1
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），None使用默认值
            
        Returns:
            bool: 是否设置成功
        """
        # 检查容量
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()
        
        # 设置值
        self._cache[key] = value
        
        # 设置过期时间
        ttl = ttl or self.default_ttl
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
        
        # 初始化访问计数
        self._access_count[key] = 0
        
        return True
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        if key in self._cache:
            self._remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._expiry.clear()
        self._access_count.clear()
    
    def _remove(self, key: str) -> None:
        """移除缓存条目"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        self._access_count.pop(key, None)
    
    def _evict_lru(self) -> None:
        """使用LRU策略驱逐缓存"""
        if not self._cache:
            return
        
        # 找到访问次数最少的key
        lru_key = min(self._access_count.items(), key=lambda x: x[1])[0]
        self._remove(lru_key)
        logger.debug(f"Evicted LRU cache entry: {lru_key}")


class LockAnalysisCache:
    """
    锁分析缓存管理器
    
    实现多级缓存策略
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        local_cache_size: int = 1000,
        enable_local: bool = True,
        enable_redis: bool = True
    ):
        """
        初始化缓存管理器
        
        Args:
            redis_url: Redis连接URL
            local_cache_size: 本地缓存大小
            enable_local: 是否启用本地缓存
            enable_redis: 是否启用Redis缓存
        """
        self.enable_local = enable_local
        self.enable_redis = enable_redis and REDIS_AVAILABLE
        
        # 本地缓存（L1）
        self.local_cache = LocalCache(max_size=local_cache_size) if enable_local else None
        
        # Redis缓存（L2）
        self.redis_client = None
        if self.enable_redis and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                logger.info(f"Redis cache initialized: {redis_url}")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")
                self.enable_redis = False
        
        # TTL配置（秒）
        self.ttl_config = {
            'realtime': 10,      # 实时数据: 10秒
            'analysis': 300,     # 分析结果: 5分钟
            'historical': 3600,  # 历史数据: 1小时
            'statistics': 1800   # 统计数据: 30分钟
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存（多级查询）
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值
        """
        # 1. 检查本地缓存
        if self.enable_local and self.local_cache:
            value = self.local_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit (local): {key}")
                return value
        
        # 2. 检查Redis缓存
        if self.enable_redis and self.redis_client:
            try:
                cached_bytes = await self.redis_client.get(key)
                if cached_bytes:
                    value = pickle.loads(cached_bytes)
                    logger.debug(f"Cache hit (redis): {key}")
                    
                    # 回填本地缓存
                    if self.enable_local and self.local_cache:
                        self.local_cache.set(key, value)
                    
                    return value
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        data_type: str = 'analysis',
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存（多级写入）
        
        Args:
            key: 缓存键
            value: 缓存值
            data_type: 数据类型（决定TTL）
            ttl: 自定义TTL（秒），覆盖data_type的默认值
            
        Returns:
            bool: 是否设置成功
        """
        # 确定TTL
        if ttl is None:
            ttl = self.ttl_config.get(data_type, 300)
        
        success = True
        
        # 1. 写入本地缓存
        if self.enable_local and self.local_cache:
            self.local_cache.set(key, value, ttl)
        
        # 2. 写入Redis缓存
        if self.enable_redis and self.redis_client:
            try:
                serialized = pickle.dumps(value)
                await self.redis_client.setex(key, ttl, serialized)
                logger.debug(f"Cache set (redis): {key}, TTL: {ttl}s")
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                success = False
        
        return success
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        success = True
        
        # 1. 删除本地缓存
        if self.enable_local and self.local_cache:
            self.local_cache.delete(key)
        
        # 2. 删除Redis缓存
        if self.enable_redis and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                success = False
        
        return success
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        失效匹配模式的所有缓存
        
        Args:
            pattern: 匹配模式（支持通配符 *）
            
        Returns:
            int: 失效的缓存数量
        """
        count = 0
        
        # 1. 清除本地缓存
        if self.enable_local and self.local_cache:
            import fnmatch
            keys_to_remove = [
                k for k in self.local_cache._cache.keys()
                if fnmatch.fnmatch(k, pattern)
            ]
            for key in keys_to_remove:
                self.local_cache.delete(key)
                count += 1
        
        # 2. 清除Redis缓存
        if self.enable_redis and self.redis_client:
            try:
                async for key in self.redis_client.scan_iter(match=pattern):
                    await self.redis_client.delete(key)
                    count += 1
            except Exception as e:
                logger.error(f"Redis pattern delete error: {e}")
        
        logger.info(f"Invalidated {count} cache entries matching: {pattern}")
        return count
    
    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        data_type: str = 'analysis',
        force_refresh: bool = False
    ) -> Any:
        """
        获取缓存或计算新值
        
        Args:
            key: 缓存键
            compute_func: 计算函数
            data_type: 数据类型
            force_refresh: 是否强制刷新
            
        Returns:
            Any: 缓存值或计算结果
        """
        # 强制刷新则跳过缓存
        if not force_refresh:
            cached_value = await self.get(key)
            if cached_value is not None:
                return cached_value
        
        # 计算新值
        logger.debug(f"Computing value for key: {key}")
        value = await compute_func()
        
        # 写入缓存
        await self.set(key, value, data_type)
        
        return value
    
    async def close(self):
        """关闭缓存连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")


def cache_result(data_type: str = 'analysis', key_prefix: str = ''):
    """
    缓存结果装饰器
    
    Args:
        data_type: 数据类型
        key_prefix: 缓存键前缀
        
    Usage:
        @cache_result(data_type='analysis', key_prefix='lock_analysis')
        async def analyze_locks(database_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            
            # 尝试从缓存获取
            # 注意：这里需要从外部传入cache实例
            # 实际使用时需要改进这个设计
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            return result
        
        return wrapper
    return decorator