"""
数据库实例模型定义
"""
from sqlalchemy import String, Boolean, Integer, TIMESTAMP, JSON, func, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.db.base import Base, TimestampMixin, UserMixin


class DatabaseType(Base, TimestampMixin):
    """
    数据库类型表
    """
    __tablename__ = "database_types"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50),  nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    driver_class: Mapped[str] = mapped_column(String(200), nullable=True)
    default_port: Mapped[int] = mapped_column(Integer, nullable=True)
    supported_features: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    config_template: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DatabaseInstance(Base, TimestampMixin, UserMixin):
    """
    数据库实例表
    """
    __tablename__ = "database_instances"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    host: Mapped[str] = mapped_column(String(100), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    database_name: Mapped[str] = mapped_column(String(100), nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    password_encrypted: Mapped[str] = mapped_column(Text, nullable=True)  # 加密存储
    ssl_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ssl_config: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    connection_params: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    tags: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    environment: Mapped[str] = mapped_column(String(20), default='production', nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='active', nullable=False)
    health_status: Mapped[str] = mapped_column(String(20), default='unknown', nullable=False)

    # 外键关系
    # creator = relationship("User", back_populates="created_databases", foreign_keys="[DatabaseInstance.created_by]")

    # 性能调优相关关系
    slow_queries = relationship("SlowQuery", back_populates="database")
    performance_metrics = relationship("PerformanceMetric", back_populates="database")
    index_suggestions = relationship("IndexSuggestion", back_populates="database")
    execution_plans = relationship("ExecutionPlan", back_populates="database")
    tuning_tasks = relationship("TuningTask", back_populates="database")
    system_diagnoses = relationship("SystemDiagnosis", back_populates="database")
    
    # 锁分析相关关系
    lock_events = relationship("LockEvent", back_populates="database")
    lock_wait_chains = relationship("LockWaitChain", back_populates="database")
    lock_contentions = relationship("LockContention", back_populates="database")
    lock_optimization_tasks = relationship("LockOptimizationTask", back_populates="database")
    lock_analysis_reports = relationship("LockAnalysisReport", back_populates="database")




class DatabaseGroup(Base, TimestampMixin, UserMixin):
    """
    数据库分组表
    """
    __tablename__ = "database_groups"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    path: Mapped[str] = mapped_column(String(1000), nullable=True)  # 路径缓存


class DatabaseGroupMember(Base, TimestampMixin):
    """
    数据库实例分组成员表
    """
    __tablename__ = "database_group_members"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    database_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    added_by: Mapped[int] = mapped_column(Integer, nullable=True)
    added_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, default=func.now())


