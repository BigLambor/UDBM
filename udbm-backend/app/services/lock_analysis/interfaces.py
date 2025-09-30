"""
锁分析核心接口定义

定义所有抽象接口，遵循依赖倒置原则
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import timedelta

from .models import (
    LockSnapshot,
    WaitChain,
    LockStatistics,
    AnalysisResult,
    OptimizationAdvice,
    ContentionMetrics
)


class ILockDataCollector(ABC):
    """
    锁数据采集器接口
    
    职责：从目标数据库采集锁相关数据
    """
    
    @abstractmethod
    async def collect_current_locks(self) -> List[LockSnapshot]:
        """
        采集当前锁状态
        
        Returns:
            List[LockSnapshot]: 当前所有锁的快照列表
        """
        pass
    
    @abstractmethod
    async def collect_wait_chains(self) -> List[WaitChain]:
        """
        采集锁等待链
        
        Returns:
            List[WaitChain]: 当前所有等待链
        """
        pass
    
    @abstractmethod
    async def collect_statistics(self, duration: timedelta) -> LockStatistics:
        """
        采集锁统计信息
        
        Args:
            duration: 统计时间范围
            
        Returns:
            LockStatistics: 锁统计数据
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 采集器是否正常工作
        """
        pass


class IAnalyzer(ABC):
    """
    分析器接口
    
    职责：对采集的数据进行分析
    """
    
    @abstractmethod
    async def analyze(self, data: Any) -> Any:
        """
        执行分析
        
        Args:
            data: 输入数据
            
        Returns:
            Any: 分析结果
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取分析器名称
        
        Returns:
            str: 分析器名称
        """
        pass


class IOptimizationStrategy(ABC):
    """
    优化策略接口
    
    职责：生成具体的优化建议
    """
    
    @abstractmethod
    def is_applicable(self, analysis: AnalysisResult) -> bool:
        """
        判断策略是否适用
        
        Args:
            analysis: 分析结果
            
        Returns:
            bool: 是否适用此策略
        """
        pass
    
    @abstractmethod
    async def generate(self, analysis: AnalysisResult) -> List[OptimizationAdvice]:
        """
        生成优化建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            List[OptimizationAdvice]: 优化建议列表
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        获取策略优先级
        
        Returns:
            int: 优先级（数字越小优先级越高）
        """
        pass


class ICacheManager(ABC):
    """
    缓存管理器接口
    
    职责：管理分析结果的缓存
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，不存在返回None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        失效匹配模式的所有缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            int: 失效的缓存数量
        """
        pass


class IMetricsCollector(ABC):
    """
    指标采集器接口
    
    职责：采集和记录性能指标
    """
    
    @abstractmethod
    async def record_duration(self, metric_name: str, duration: float) -> None:
        """
        记录耗时指标
        
        Args:
            metric_name: 指标名称
            duration: 耗时（秒）
        """
        pass
    
    @abstractmethod
    async def record_counter(self, metric_name: str, value: int = 1) -> None:
        """
        记录计数器指标
        
        Args:
            metric_name: 指标名称
            value: 计数值
        """
        pass
    
    @abstractmethod
    async def record_gauge(self, metric_name: str, value: float) -> None:
        """
        记录仪表盘指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
        """
        pass


class IAlertManager(ABC):
    """
    告警管理器接口
    
    职责：发送和管理告警
    """
    
    @abstractmethod
    async def send_alert(
        self,
        level: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送告警
        
        Args:
            level: 告警级别 (info, warning, error, critical)
            title: 告警标题
            message: 告警消息
            metadata: 附加元数据
            
        Returns:
            bool: 是否发送成功
        """
        pass
    
    @abstractmethod
    async def check_alert_rules(
        self,
        database_id: int,
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检查告警规则
        
        Args:
            database_id: 数据库ID
            metrics: 指标数据
            
        Returns:
            List[Dict[str, Any]]: 触发的告警列表
        """
        pass