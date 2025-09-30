"""
优化建议生成器模块

包含各种优化策略实现
"""

from .index_strategy import IndexOptimizationStrategy
from .query_strategy import QueryOptimizationStrategy

__all__ = [
    "IndexOptimizationStrategy",
    "QueryOptimizationStrategy"
]