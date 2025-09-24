"""
数据库锁分析相关Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class LockEventResponse(BaseModel):
    """锁事件响应模型"""
    id: int
    database_id: int
    lock_type: str
    lock_mode: str
    lock_status: str
    object_type: str
    object_name: str
    schema_name: Optional[str] = None
    session_id: str
    process_id: Optional[int] = None
    user_name: Optional[str] = None
    host_name: Optional[str] = None
    lock_request_time: datetime
    lock_grant_time: Optional[datetime] = None
    lock_release_time: Optional[datetime] = None
    wait_duration: Optional[float] = None
    hold_duration: Optional[float] = None
    query_text: Optional[str] = None
    query_hash: Optional[str] = None
    blocking_session_id: Optional[str] = None
    blocking_query_text: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None
    optimization_suggestions: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LockWaitChainResponse(BaseModel):
    """锁等待链响应模型"""
    id: int
    database_id: int
    chain_id: str
    chain_length: int
    total_wait_time: float
    head_session_id: str
    head_query_text: Optional[str] = None
    head_lock_type: str
    head_object_name: str
    tail_session_id: str
    tail_query_text: Optional[str] = None
    tail_lock_type: str
    tail_object_name: str
    chain_details: Dict[str, Any]
    severity_level: str
    analysis_result: Optional[Dict[str, Any]] = None
    resolution_suggestions: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LockContentionResponse(BaseModel):
    """锁竞争响应模型"""
    id: int
    database_id: int
    object_type: str
    object_name: str
    schema_name: Optional[str] = None
    contention_count: int
    total_wait_time: float
    avg_wait_time: float
    max_wait_time: float
    contention_pattern: str
    lock_types: Dict[str, int]
    affected_sessions: int
    affected_queries: int
    performance_impact: float
    root_cause: Optional[str] = None
    optimization_suggestions: Optional[List[str]] = None
    priority_level: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LockOptimizationTaskResponse(BaseModel):
    """锁优化任务响应模型"""
    id: int
    database_id: int
    task_type: str
    task_name: str
    description: Optional[str] = None
    task_config: Dict[str, Any]
    target_objects: List[str]
    status: str
    priority: int
    execution_sql: Optional[str] = None
    execution_result: Optional[str] = None
    error_message: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    related_contention_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LockAnalysisReportResponse(BaseModel):
    """锁分析报告响应模型"""
    id: int
    database_id: int
    report_type: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    overall_health_score: float
    lock_efficiency_score: float
    contention_severity: str
    total_lock_events: int
    total_wait_time: float
    deadlock_count: int
    timeout_count: int
    hot_objects: Optional[List[Dict[str, Any]]] = None
    report_content: Dict[str, Any]
    recommendations: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LockAnalysisRequest(BaseModel):
    """锁分析请求模型"""
    database_id: int
    analysis_type: str = Field(..., description="分析类型：realtime, historical, comprehensive")
    time_range_hours: int = Field(24, ge=1, le=168, description="分析时间范围(小时)")
    include_wait_chains: bool = Field(True, description="是否包含等待链分析")
    include_contention: bool = Field(True, description="是否包含竞争分析")
    min_wait_time: float = Field(0.1, ge=0, description="最小等待时间阈值(秒)")


class LockOptimizationRequest(BaseModel):
    """锁优化请求模型"""
    database_id: int
    optimization_type: str = Field(..., description="优化类型：index, query, isolation, config")
    target_objects: List[str] = Field(..., description="目标对象列表")
    optimization_config: Dict[str, Any] = Field(default_factory=dict, description="优化配置")
    priority: int = Field(1, ge=1, le=5, description="优先级 1-5")


class LockDashboardResponse(BaseModel):
    """锁分析仪表板响应模型"""
    database_id: int
    analysis_timestamp: datetime
    overall_health_score: float
    lock_efficiency_score: float
    contention_severity: str
    
    # 实时统计
    current_locks: int
    waiting_locks: int
    deadlock_count_today: int
    timeout_count_today: int
    
    # 热点对象
    hot_objects: List[Dict[str, Any]]
    
    # 等待链
    active_wait_chains: List[LockWaitChainResponse]
    
    # 竞争分析
    top_contentions: List[LockContentionResponse]
    
    # 优化建议
    optimization_suggestions: List[Dict[str, Any]]
    
    # 趋势数据
    lock_trends: Dict[str, List[Dict[str, Any]]]


class LockAnalysisSummaryResponse(BaseModel):
    """锁分析总结响应模型"""
    database_id: int
    analysis_period: str
    total_events: int
    total_wait_time: float
    avg_wait_time: float
    max_wait_time: float
    
    # 锁类型分布
    lock_type_distribution: Dict[str, int]
    
    # 对象竞争排行
    top_contention_objects: List[Dict[str, Any]]
    
    # 会话等待排行
    top_waiting_sessions: List[Dict[str, Any]]
    
    # 问题严重程度
    critical_issues: int
    high_priority_issues: int
    medium_priority_issues: int
    low_priority_issues: int
    
    # 优化建议统计
    total_suggestions: int
    high_impact_suggestions: int
    implemented_suggestions: int


class LockOptimizationScriptResponse(BaseModel):
    """锁优化脚本响应模型"""
    script_id: str
    database_id: int
    script_type: str
    script_content: str
    target_objects: List[str]
    estimated_impact: str
    execution_instructions: List[str]
    rollback_script: Optional[str] = None
    generated_at: datetime
    generated_by: str


class LockMonitoringConfigResponse(BaseModel):
    """锁监控配置响应模型"""
    database_id: int
    monitoring_enabled: bool
    collection_interval: int  # 秒
    retention_days: int
    alert_thresholds: Dict[str, float]
    notification_settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
