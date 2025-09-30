"""
工厂类和注册机制

负责创建和管理各种组件实例
"""
from typing import Dict, Type, Optional, Any
import logging

from .interfaces import ILockDataCollector, IAnalyzer, IOptimizationStrategy

logger = logging.getLogger(__name__)


class CollectorRegistry:
    """
    采集器注册表
    
    使用工厂模式管理不同数据库类型的采集器
    """
    
    _collectors: Dict[str, Type[ILockDataCollector]] = {}
    
    @classmethod
    def register(cls, db_type: str, collector_class: Type[ILockDataCollector]) -> None:
        """
        注册采集器
        
        Args:
            db_type: 数据库类型 (postgresql, mysql, oceanbase)
            collector_class: 采集器类
        """
        cls._collectors[db_type.lower()] = collector_class
        logger.info(f"Registered collector for {db_type}: {collector_class.__name__}")
    
    @classmethod
    def get_collector_class(cls, db_type: str) -> Optional[Type[ILockDataCollector]]:
        """
        获取采集器类
        
        Args:
            db_type: 数据库类型
            
        Returns:
            Optional[Type[ILockDataCollector]]: 采集器类，不存在返回None
        """
        return cls._collectors.get(db_type.lower())
    
    @classmethod
    def create_collector(
        cls,
        db_type: str,
        **kwargs
    ) -> Optional[ILockDataCollector]:
        """
        创建采集器实例
        
        Args:
            db_type: 数据库类型
            **kwargs: 采集器构造参数
            
        Returns:
            Optional[ILockDataCollector]: 采集器实例
        """
        collector_class = cls.get_collector_class(db_type)
        if collector_class is None:
            logger.error(f"No collector registered for database type: {db_type}")
            return None
        
        try:
            collector = collector_class(**kwargs)
            logger.info(f"Created collector instance for {db_type}")
            return collector
        except Exception as e:
            logger.error(f"Failed to create collector for {db_type}: {e}", exc_info=True)
            return None
    
    @classmethod
    def list_supported_types(cls) -> list:
        """
        列出支持的数据库类型
        
        Returns:
            list: 支持的数据库类型列表
        """
        return list(cls._collectors.keys())


class AnalyzerRegistry:
    """
    分析器注册表
    
    管理各种分析器
    """
    
    _analyzers: Dict[str, Type[IAnalyzer]] = {}
    
    @classmethod
    def register(cls, name: str, analyzer_class: Type[IAnalyzer]) -> None:
        """
        注册分析器
        
        Args:
            name: 分析器名称
            analyzer_class: 分析器类
        """
        cls._analyzers[name] = analyzer_class
        logger.info(f"Registered analyzer: {name}")
    
    @classmethod
    def get_analyzer_class(cls, name: str) -> Optional[Type[IAnalyzer]]:
        """
        获取分析器类
        
        Args:
            name: 分析器名称
            
        Returns:
            Optional[Type[IAnalyzer]]: 分析器类
        """
        return cls._analyzers.get(name)
    
    @classmethod
    def create_analyzer(cls, name: str, **kwargs) -> Optional[IAnalyzer]:
        """
        创建分析器实例
        
        Args:
            name: 分析器名称
            **kwargs: 构造参数
            
        Returns:
            Optional[IAnalyzer]: 分析器实例
        """
        analyzer_class = cls.get_analyzer_class(name)
        if analyzer_class is None:
            logger.error(f"No analyzer registered with name: {name}")
            return None
        
        try:
            analyzer = analyzer_class(**kwargs)
            logger.info(f"Created analyzer instance: {name}")
            return analyzer
        except Exception as e:
            logger.error(f"Failed to create analyzer {name}: {e}", exc_info=True)
            return None
    
    @classmethod
    def create_all_analyzers(cls, **kwargs) -> list:
        """
        创建所有已注册的分析器
        
        Args:
            **kwargs: 构造参数
            
        Returns:
            list: 分析器实例列表
        """
        analyzers = []
        for name, analyzer_class in cls._analyzers.items():
            try:
                analyzer = analyzer_class(**kwargs)
                analyzers.append(analyzer)
                logger.info(f"Created analyzer: {name}")
            except Exception as e:
                logger.error(f"Failed to create analyzer {name}: {e}", exc_info=True)
        return analyzers
    
    @classmethod
    def list_analyzers(cls) -> list:
        """
        列出所有已注册的分析器
        
        Returns:
            list: 分析器名称列表
        """
        return list(cls._analyzers.keys())


class StrategyRegistry:
    """
    优化策略注册表
    
    管理各种优化策略
    """
    
    _strategies: Dict[str, Type[IOptimizationStrategy]] = {}
    
    @classmethod
    def register(cls, strategy_type: str, strategy_class: Type[IOptimizationStrategy]) -> None:
        """
        注册优化策略
        
        Args:
            strategy_type: 策略类型 (index, query, isolation, config, schema)
            strategy_class: 策略类
        """
        cls._strategies[strategy_type] = strategy_class
        logger.info(f"Registered optimization strategy: {strategy_type}")
    
    @classmethod
    def get_strategy_class(cls, strategy_type: str) -> Optional[Type[IOptimizationStrategy]]:
        """
        获取策略类
        
        Args:
            strategy_type: 策略类型
            
        Returns:
            Optional[Type[IOptimizationStrategy]]: 策略类
        """
        return cls._strategies.get(strategy_type)
    
    @classmethod
    def create_strategy(cls, strategy_type: str, **kwargs) -> Optional[IOptimizationStrategy]:
        """
        创建策略实例
        
        Args:
            strategy_type: 策略类型
            **kwargs: 构造参数
            
        Returns:
            Optional[IOptimizationStrategy]: 策略实例
        """
        strategy_class = cls.get_strategy_class(strategy_type)
        if strategy_class is None:
            logger.error(f"No strategy registered for type: {strategy_type}")
            return None
        
        try:
            strategy = strategy_class(**kwargs)
            logger.info(f"Created strategy instance: {strategy_type}")
            return strategy
        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_type}: {e}", exc_info=True)
            return None
    
    @classmethod
    def create_all_strategies(cls, **kwargs) -> list:
        """
        创建所有已注册的策略
        
        Args:
            **kwargs: 构造参数
            
        Returns:
            list: 策略实例列表
        """
        strategies = []
        for strategy_type, strategy_class in cls._strategies.items():
            try:
                strategy = strategy_class(**kwargs)
                strategies.append(strategy)
                logger.info(f"Created strategy: {strategy_type}")
            except Exception as e:
                logger.error(f"Failed to create strategy {strategy_type}: {e}", exc_info=True)
        
        # 按优先级排序
        strategies.sort(key=lambda s: s.get_priority())
        return strategies
    
    @classmethod
    def list_strategies(cls) -> list:
        """
        列出所有已注册的策略
        
        Returns:
            list: 策略类型列表
        """
        return list(cls._strategies.keys())


# 便捷函数

def register_collector(db_type: str):
    """
    装饰器：注册采集器
    
    Usage:
        @register_collector('postgresql')
        class PostgreSQLCollector(ILockDataCollector):
            pass
    """
    def decorator(cls):
        CollectorRegistry.register(db_type, cls)
        return cls
    return decorator


def register_analyzer(name: str):
    """
    装饰器：注册分析器
    
    Usage:
        @register_analyzer('wait_chain')
        class WaitChainAnalyzer(IAnalyzer):
            pass
    """
    def decorator(cls):
        AnalyzerRegistry.register(name, cls)
        return cls
    return decorator


def register_strategy(strategy_type: str):
    """
    装饰器：注册优化策略
    
    Usage:
        @register_strategy('index')
        class IndexOptimizationStrategy(IOptimizationStrategy):
            pass
    """
    def decorator(cls):
        StrategyRegistry.register(strategy_type, cls)
        return cls
    return decorator