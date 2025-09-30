"""
锁分析服务模块

重构后的模块化架构，包含：
- collectors: 数据采集器
- analyzers: 分析引擎
- advisors: 优化建议生成器
- cache: 缓存管理
- orchestrator: 分析编排器
"""

__version__ = "2.0.0"
__author__ = "UDBM Team"

from .models import (
    LockSnapshot,
    WaitChain,
    ContentionMetrics,
    LockStatistics,
    AnalysisResult,
    OptimizationAdvice,
    LockType,
    LockMode
)

from .orchestrator import LockAnalysisOrchestrator
from .cache import LockAnalysisCache
from .factories import CollectorRegistry, AnalyzerRegistry, StrategyRegistry

__all__ = [
    # 数据模型
    "LockSnapshot",
    "WaitChain", 
    "ContentionMetrics",
    "LockStatistics",
    "AnalysisResult",
    "OptimizationAdvice",
    "LockType",
    "LockMode",
    # 核心组件
    "LockAnalysisOrchestrator",
    "LockAnalysisCache",
    # 注册表
    "CollectorRegistry",
    "AnalyzerRegistry",
    "StrategyRegistry"
]