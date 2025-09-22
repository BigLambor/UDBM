"""
监控指标模型定义
"""
import os
from sqlalchemy import String, Boolean, Integer, TIMESTAMP, JSON, Float, func, Text, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import List

from app.db.base import Base, TimestampMixin, UserMixin


class MetricDefinition(Base, TimestampMixin):
    """
    监控指标定义表
    """
    __tablename__ = "metric_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100),  nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    metric_type: Mapped[str] = mapped_column(String(20), default='gauge', nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), default='numeric', nullable=False)
    database_types: Mapped[str] = mapped_column(String, nullable=True)  # JSON数组字符串
    collection_interval: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # 采集间隔(秒)
    retention_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 约束条件检查
    __table_args__ = {
    }


class Metric(Base):
    """
    监控指标数据表 (时间序列)
    注意：这是一个超表，需要手动转换为TimescaleDB超表
    """
    __tablename__ = "metrics"

    time: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False, index=True)
    database_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    metric_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    value_numeric: Mapped[float] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(Text, nullable=True)
    value_boolean: Mapped[bool] = mapped_column(Boolean, nullable=True)
    tags: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    quality_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # 复合主键
    __table_args__ = (
        {'primary_key': ['time', 'database_id', 'metric_id']}
    )


class AlertRule(Base, TimestampMixin, UserMixin):
    """
    告警规则表
    """
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    metric_id: Mapped[int] = mapped_column(Integer, nullable=True)
    database_id: Mapped[int] = mapped_column(Integer, nullable=True)  # NULL表示全局规则
    condition_operator: Mapped[str] = mapped_column(String(10), nullable=False)
    condition_value: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default='warning', nullable=False)
    evaluation_period: Mapped[int] = mapped_column(Integer, default=300, nullable=False)  # 评估周期(秒)
    notification_channels: Mapped[str] = mapped_column(String, default='[]', nullable=False)  # JSON数组字符串
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 约束条件检查
    __table_args__ = {
    }


class Alert(Base, TimestampMixin):
    """
    告警历史表
    """
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    database_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='firing', nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    labels: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    annotations: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    started_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, default=func.now())
    ended_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=True)
    acknowledged_by: Mapped[int] = mapped_column(Integer, nullable=True)
    acknowledged_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=True)

    # 约束条件检查
    __table_args__ = {
    }
