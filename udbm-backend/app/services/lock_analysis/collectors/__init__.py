"""
数据采集器模块

包含不同数据库类型的锁数据采集器实现
"""

from .base import BaseLockCollector
from .postgresql import PostgreSQLLockCollector

__all__ = [
    "BaseLockCollector",
    "PostgreSQLLockCollector"
]