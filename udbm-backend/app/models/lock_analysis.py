"""
数据库锁分析相关数据模型
"""
from sqlalchemy import String, Boolean, Integer, TIMESTAMP, JSON, func, Text, ForeignKey, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from app.db.base import Base, TimestampMixin, UserMixin


class LockEvent(Base, TimestampMixin):
    """
    锁事件记录表
    """
    __tablename__ = "lock_events"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("udbm.database_instances.id"), nullable=False, index=True)
    
    # 锁基本信息
    lock_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 锁类型：表锁、行锁、页锁等
    lock_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # 锁模式：共享锁、排他锁、意向锁等
    lock_status: Mapped[str] = mapped_column(String(20), nullable=False)  # 锁状态：granted, waiting, timeout
    
    # 锁对象信息
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 对象类型：table, index, row
    object_name: Mapped[str] = mapped_column(String(200), nullable=False)  # 对象名称
    schema_name: Mapped[str] = mapped_column(String(100), nullable=True)  # 模式名称
    
    # 会话信息
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)  # 会话ID
    process_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 进程ID
    user_name: Mapped[str] = mapped_column(String(100), nullable=True)  # 用户名
    host_name: Mapped[str] = mapped_column(String(200), nullable=True)  # 主机名
    
    # 时间信息
    lock_request_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)  # 锁请求时间
    lock_grant_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)  # 锁获得时间
    lock_release_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)  # 锁释放时间
    wait_duration: Mapped[float] = mapped_column(Float, nullable=True)  # 等待时长(秒)
    hold_duration: Mapped[float] = mapped_column(Float, nullable=True)  # 持有时长(秒)
    
    # 查询信息
    query_text: Mapped[str] = mapped_column(Text, nullable=True)  # 相关查询语句
    query_hash: Mapped[str] = mapped_column(String(64), nullable=True)  # 查询哈希
    
    # 锁等待链信息
    blocking_session_id: Mapped[str] = mapped_column(String(100), nullable=True)  # 阻塞会话ID
    blocking_query_text: Mapped[str] = mapped_column(Text, nullable=True)  # 阻塞查询语句
    
    # 分析结果
    analysis_result: Mapped[str] = mapped_column(Text, nullable=True)  # JSON格式的分析结果
    optimization_suggestions: Mapped[str] = mapped_column(Text, nullable=True)  # 优化建议
    
    # 外键关系
    database = relationship("DatabaseInstance", back_populates="lock_events")


class LockWaitChain(Base, TimestampMixin):
    """
    锁等待链表
    """
    __tablename__ = "lock_wait_chains"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("udbm.database_instances.id"), nullable=False, index=True)
    
    # 等待链信息
    chain_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # 等待链ID
    chain_length: Mapped[int] = mapped_column(Integer, nullable=False)  # 链长度
    total_wait_time: Mapped[float] = mapped_column(Float, nullable=False)  # 总等待时间
    
    # 链头信息（被阻塞的会话）
    head_session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    head_query_text: Mapped[str] = mapped_column(Text, nullable=True)
    head_lock_type: Mapped[str] = mapped_column(String(50), nullable=False)
    head_object_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # 链尾信息（阻塞源）
    tail_session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tail_query_text: Mapped[str] = mapped_column(Text, nullable=True)
    tail_lock_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tail_object_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # 链详情（JSON格式存储整个链）
    chain_details: Mapped[str] = mapped_column(Text, nullable=False)  # JSON格式的链详情
    
    # 分析结果
    severity_level: Mapped[str] = mapped_column(String(20), nullable=False)  # 严重程度：low, medium, high, critical
    analysis_result: Mapped[str] = mapped_column(Text, nullable=True)  # JSON格式的分析结果
    resolution_suggestions: Mapped[str] = mapped_column(Text, nullable=True)  # 解决建议
    
    # 外键关系
    database = relationship("DatabaseInstance", back_populates="lock_wait_chains")


class LockContention(Base, TimestampMixin):
    """
    锁竞争分析表
    """
    __tablename__ = "lock_contentions"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("udbm.database_instances.id"), nullable=False, index=True)
    
    # 竞争对象信息
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 对象类型
    object_name: Mapped[str] = mapped_column(String(200), nullable=False)  # 对象名称
    schema_name: Mapped[str] = mapped_column(String(100), nullable=True)  # 模式名称
    
    # 竞争统计
    contention_count: Mapped[int] = mapped_column(Integer, nullable=False)  # 竞争次数
    total_wait_time: Mapped[float] = mapped_column(Float, nullable=False)  # 总等待时间
    avg_wait_time: Mapped[float] = mapped_column(Float, nullable=False)  # 平均等待时间
    max_wait_time: Mapped[float] = mapped_column(Float, nullable=False)  # 最大等待时间
    
    # 竞争模式
    contention_pattern: Mapped[str] = mapped_column(String(50), nullable=False)  # 竞争模式：hot_spot, deadlock, timeout
    lock_types: Mapped[str] = mapped_column(Text, nullable=False)  # JSON格式的锁类型统计
    
    # 影响分析
    affected_sessions: Mapped[int] = mapped_column(Integer, nullable=False)  # 影响的会话数
    affected_queries: Mapped[int] = mapped_column(Integer, nullable=False)  # 影响的查询数
    performance_impact: Mapped[float] = mapped_column(Float, nullable=False)  # 性能影响评分
    
    # 分析结果
    root_cause: Mapped[str] = mapped_column(Text, nullable=True)  # 根本原因分析
    optimization_suggestions: Mapped[str] = mapped_column(Text, nullable=True)  # 优化建议
    priority_level: Mapped[str] = mapped_column(String(20), nullable=False)  # 优先级：low, medium, high, critical
    
    # 外键关系
    database = relationship("DatabaseInstance", back_populates="lock_contentions")


class LockOptimizationTask(Base, TimestampMixin):
    """
    锁优化任务表
    """
    __tablename__ = "lock_optimization_tasks"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("udbm.database_instances.id"), nullable=False, index=True)
    
    # 任务基本信息
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 任务类型：index_optimization, query_rewrite, isolation_level, etc.
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # 任务配置
    task_config: Mapped[str] = mapped_column(Text, nullable=False)  # JSON格式的任务配置
    target_objects: Mapped[str] = mapped_column(Text, nullable=False)  # JSON格式的目标对象列表
    
    # 执行状态
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)  # pending, running, completed, failed
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5, 5为最高优先级
    
    # 执行结果
    execution_sql: Mapped[str] = mapped_column(Text, nullable=True)  # 要执行的SQL语句
    execution_result: Mapped[str] = mapped_column(Text, nullable=True)  # 执行结果
    error_message: Mapped[str] = mapped_column(Text, nullable=True)  # 错误信息
    
    # 时间戳
    scheduled_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    
    # 关联对象
    related_contention_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 关联的竞争分析ID
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)  # 创建者ID
    
    # 外键关系
    database = relationship("DatabaseInstance", back_populates="lock_optimization_tasks")


class LockAnalysisReport(Base, TimestampMixin):
    """
    锁分析报告表
    """
    __tablename__ = "lock_analysis_reports"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(Integer, ForeignKey("udbm.database_instances.id"), nullable=False, index=True)
    
    # 报告基本信息
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 报告类型：daily, weekly, monthly, custom
    analysis_period_start: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    analysis_period_end: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    
    # 分析结果
    overall_health_score: Mapped[float] = mapped_column(Float, nullable=False)  # 整体健康评分 0-100
    lock_efficiency_score: Mapped[float] = mapped_column(Float, nullable=False)  # 锁效率评分
    contention_severity: Mapped[str] = mapped_column(String(20), nullable=False)  # 竞争严重程度
    
    # 统计信息
    total_lock_events: Mapped[int] = mapped_column(Integer, nullable=False)  # 总锁事件数
    total_wait_time: Mapped[float] = mapped_column(Float, nullable=False)  # 总等待时间
    deadlock_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 死锁次数
    timeout_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 超时次数
    
    # 热点对象
    hot_objects: Mapped[str] = mapped_column(Text, nullable=True)  # JSON格式的热点对象列表
    
    # 报告内容
    report_content: Mapped[str] = mapped_column(Text, nullable=False)  # JSON格式的报告内容
    recommendations: Mapped[str] = mapped_column(Text, nullable=True)  # 优化建议
    
    # 外键关系
    database = relationship("DatabaseInstance", back_populates="lock_analysis_reports")
