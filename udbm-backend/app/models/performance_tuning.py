"""
性能调优相关数据模型
"""
import os
from sqlalchemy import String, Boolean, Integer, TIMESTAMP, JSON, func, Text, ForeignKey, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from app.db.base import Base, TimestampMixin, UserMixin


class SlowQuery(Base, TimestampMixin):
    """
    慢查询记录表
    """
    __tablename__ = "slow_queries"
    __table_args__ = {} if os.getenv("USE_SQLITE", "true").lower() == "true" else {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_instances.id"), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 查询哈希用于去重
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)  # 执行时间(秒)
    lock_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 锁等待时间
    rows_sent: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # 返回行数
    rows_examined: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # 检查行数
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now(), nullable=False, index=True)
    user_host: Mapped[str] = mapped_column(String(200), nullable=True)
    sql_command: Mapped[str] = mapped_column(String(50), nullable=True)  # SELECT, UPDATE, etc.
    status: Mapped[str] = mapped_column(String(20), default='active', nullable=False)  # active, resolved, ignored

    # 分析结果
    analysis_result: Mapped[str] = mapped_column(Text, nullable=True)  # JSON格式的分析结果
    optimization_suggestions: Mapped[str] = mapped_column(Text, nullable=True)  # 优化建议

    # 外键关系
    database = relationship("DatabaseInstance", back_populates="slow_queries")


class PerformanceMetric(Base, TimestampMixin):
    """
    性能指标表
    """
    __tablename__ = "performance_metrics"
    __table_args__ = {} if os.getenv("USE_SQLITE", "true").lower() == "true" else {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_instances.id"), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # cpu, memory, io, connections, qps, tps
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=True)  # %, MB, ms, count, etc.
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now(), nullable=False, index=True)

    # 标签和元数据
    tags: Mapped[str] = mapped_column(Text, default='{}', nullable=False)  # JSON格式的标签
    metric_metadata: Mapped[str] = mapped_column(Text, default='{}', nullable=False)  # JSON格式的元数据

    # 外键关系
    database = relationship("DatabaseInstance", back_populates="performance_metrics")


class IndexSuggestion(Base, TimestampMixin):
    """
    索引优化建议表
    """
    __tablename__ = "index_suggestions"
    __table_args__ = {} if os.getenv("USE_SQLITE", "true").lower() == "true" else {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_instances.id"), nullable=False, index=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    column_names: Mapped[str] = mapped_column(Text, nullable=False)  # JSON数组格式的列名
    index_type: Mapped[str] = mapped_column(String(50), default='btree', nullable=False)  # btree, hash, gin, etc.
    suggestion_type: Mapped[str] = mapped_column(String(50), nullable=False)  # missing, redundant, unused, inefficient

    # 建议详情
    reason: Mapped[str] = mapped_column(Text, nullable=False)  # 建议原因
    impact_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 影响评分 0-100
    estimated_improvement: Mapped[str] = mapped_column(Text, nullable=True)  # 预估改善效果

    # 执行状态
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)  # pending, applied, rejected, failed
    applied_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    applied_by: Mapped[int] = mapped_column(Integer, nullable=True)

    # 关联的慢查询
    related_query_ids: Mapped[str] = mapped_column(Text, default='[]', nullable=False)  # JSON数组格式

    # 外键关系
    database = relationship("DatabaseInstance", back_populates="index_suggestions")


class ExecutionPlan(Base, TimestampMixin):
    """
    执行计划分析表
    """
    __tablename__ = "execution_plans"
    __table_args__ = {} if os.getenv("USE_SQLITE", "true").lower() == "true" else {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_instances.id"), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # 执行计划详情
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)  # EXPLAIN FORMAT=JSON 的结果
    plan_text: Mapped[str] = mapped_column(Text, nullable=False)  # EXPLAIN 的文本结果

    # 性能分析
    cost_estimate: Mapped[float] = mapped_column(Float, nullable=True)
    rows_estimate: Mapped[int] = mapped_column(BigInteger, nullable=True)
    actual_rows: Mapped[int] = mapped_column(BigInteger, nullable=True)
    execution_time: Mapped[float] = mapped_column(Float, nullable=True)

    # 分析结果
    analysis_result: Mapped[str] = mapped_column(Text, nullable=True)  # JSON格式的分析结果
    optimization_suggestions: Mapped[str] = mapped_column(Text, nullable=True)  # 优化建议

    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now(), nullable=False, index=True)

    # 外键关系
    database = relationship("DatabaseInstance", back_populates="execution_plans")


class TuningTask(Base, TimestampMixin):
    """
    调优任务表
    """
    __tablename__ = "tuning_tasks"
    __table_args__ = {} if os.getenv("USE_SQLITE", "true").lower() == "true" else {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_instances.id"), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # index_creation, query_rewrite, config_tuning
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # 任务内容
    task_config: Mapped[str] = mapped_column(Text, nullable=False)  # JSON格式的任务配置
    execution_sql: Mapped[str] = mapped_column(Text, nullable=True)  # 要执行的SQL语句

    # 执行状态
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)  # pending, running, completed, failed
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5, 5为最高优先级

    # 执行结果
    execution_result: Mapped[str] = mapped_column(Text, nullable=True)  # 执行结果
    error_message: Mapped[str] = mapped_column(Text, nullable=True)  # 错误信息

    # 时间戳
    scheduled_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)

    # 关联对象
    related_suggestion_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 关联的建议ID
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)  # 创建者ID

    # 外键关系
    database = relationship("DatabaseInstance", back_populates="tuning_tasks")


class SystemDiagnosis(Base, TimestampMixin):
    """
    系统诊断报告表
    """
    __tablename__ = "system_diagnoses"
    __table_args__ = {} if os.getenv("USE_SQLITE", "true").lower() == "true" else {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_instances.id"), nullable=False, index=True)
    diagnosis_type: Mapped[str] = mapped_column(String(50), nullable=False)  # full, quick, specific
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)  # 整体健康评分 0-100

    # 诊断结果
    diagnosis_result: Mapped[str] = mapped_column(Text, nullable=False)  # JSON格式的诊断结果
    recommendations: Mapped[str] = mapped_column(Text, nullable=True)  # 修复建议

    # 各维度评分
    performance_score: Mapped[float] = mapped_column(Float, nullable=False)  # 性能评分
    security_score: Mapped[float] = mapped_column(Float, nullable=False)  # 安全评分
    maintenance_score: Mapped[float] = mapped_column(Float, nullable=False)  # 维护评分

    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now(), nullable=False, index=True)

    # 外键关系
    database = relationship("DatabaseInstance", back_populates="system_diagnoses")
