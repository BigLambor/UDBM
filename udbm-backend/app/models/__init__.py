"""
模型模块导入
"""
from .user import User, Role, UserRole, Permission, RolePermission
from .database import DatabaseType, DatabaseInstance, DatabaseGroup, DatabaseGroupMember
from .performance_tuning import (
    SlowQuery, PerformanceMetric, IndexSuggestion, ExecutionPlan,
    TuningTask, SystemDiagnosis
)
# from .monitoring import MetricDefinition, Metric, AlertRule, Alert

# 导入所有模型到__all__
__all__ = [
    "User", "Role", "UserRole", "Permission", "RolePermission",
    "DatabaseType", "DatabaseInstance", "DatabaseGroup", "DatabaseGroupMember",
    "SlowQuery", "PerformanceMetric", "IndexSuggestion", "ExecutionPlan",
    "TuningTask", "SystemDiagnosis",
    "MetricDefinition", "Metric", "AlertRule", "Alert"
]
