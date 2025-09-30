"""
竞争分析器

分析锁竞争模式，识别热点对象
"""
import logging
from typing import List, Dict, Any
from collections import defaultdict

from ..interfaces import IAnalyzer
from ..models import LockSnapshot, ContentionMetrics
from ..factories import register_analyzer

logger = logging.getLogger(__name__)


@register_analyzer('contention')
class ContentionAnalyzer(IAnalyzer):
    """
    竞争分析器
    
    职责：
    1. 分析锁竞争情况
    2. 识别热点对象
    3. 识别竞争模式
    4. 生成优化建议
    """
    
    def get_name(self) -> str:
        """获取分析器名称"""
        return "ContentionAnalyzer"
    
    async def analyze(self, locks: List[LockSnapshot]) -> List[ContentionMetrics]:
        """
        分析锁竞争
        
        Args:
            locks: 锁快照列表
            
        Returns:
            List[ContentionMetrics]: 竞争指标列表
        """
        if not locks:
            return []
        
        # 按对象分组统计等待中的锁
        contention_map: Dict[str, List[LockSnapshot]] = defaultdict(list)
        
        for lock in locks:
            if not lock.granted:  # 只统计未授予的锁（等待中）
                contention_map[lock.object_name].append(lock)
        
        # 生成竞争指标
        contentions = []
        for object_name, object_locks in contention_map.items():
            # 计算等待时间
            wait_times = [
                lock.wait_duration 
                for lock in object_locks 
                if lock.wait_duration is not None
            ]
            
            if not wait_times:
                continue
            
            # 统计锁模式分布
            mode_dist = {}
            for lock in object_locks:
                mode = lock.lock_mode.value
                mode_dist[mode] = mode_dist.get(mode, 0) + 1
            
            # 创建竞争指标
            contention = ContentionMetrics(
                object_name=object_name,
                database_id=object_locks[0].database_id,
                contention_count=len(object_locks),
                total_wait_time=sum(wait_times),
                avg_wait_time=sum(wait_times) / len(wait_times),
                max_wait_time=max(wait_times),
                affected_sessions=len(set(lock.session_id for lock in object_locks)),
                lock_mode_distribution=mode_dist,
                pattern=self._identify_pattern(
                    len(object_locks),
                    sum(wait_times) / len(wait_times),
                    max(wait_times)
                ),
                confidence=1.0
            )
            
            contentions.append(contention)
        
        # 按总等待时间排序
        contentions.sort(key=lambda c: c.total_wait_time, reverse=True)
        
        logger.info(f"Contention analysis: found {len(contentions)} contended objects")
        
        return contentions
    
    def _identify_pattern(
        self,
        contention_count: int,
        avg_wait_time: float,
        max_wait_time: float
    ) -> str:
        """
        识别竞争模式
        
        Args:
            contention_count: 竞争次数
            avg_wait_time: 平均等待时间
            max_wait_time: 最大等待时间
            
        Returns:
            str: 竞争模式
        """
        # 热点竞争：高频率 + 长等待时间
        if contention_count > 10 and avg_wait_time > 1.0:
            return "hot_spot"
        
        # 突发竞争：短时间内大量竞争
        elif contention_count > 20:
            return "burst"
        
        # 超时易发：等待时间很长
        elif max_wait_time > 20:
            return "timeout_prone"
        
        # 频繁竞争：竞争次数多但等待时间短
        elif contention_count > 5:
            return "frequent"
        
        # 正常
        else:
            return "normal"