"""
性能调优相关的数据模型
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class SlowQueryBase(BaseModel):
    """慢查询基础模型"""
    database_id: int
    query_text: str
    execution_time: float
    lock_time: Optional[float] = 0.0
    rows_sent: Optional[int] = 0
    rows_examined: Optional[int] = 0
    user_host: Optional[str] = None
    sql_command: Optional[str] = None


class SlowQueryCreate(SlowQueryBase):
    """创建慢查询记录请求模型"""
    pass


class SlowQueryResponse(SlowQueryBase):
    """慢查询响应模型"""
    id: int
    query_hash: str
    timestamp: datetime
    analysis_result: Optional[str] = None
    optimization_suggestions: Optional[str] = None
    status: str
    source: str = "mock_data"  # 数据源标识

    class Config:
        from_attributes = True


class PerformanceMetricBase(BaseModel):
    """性能指标基础模型"""
    database_id: int
    metric_type: str
    metric_name: str
    metric_value: float
    unit: Optional[str] = None
    tags: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PerformanceMetricCreate(PerformanceMetricBase):
    """创建性能指标请求模型"""
    pass


class PerformanceMetricResponse(PerformanceMetricBase):
    """性能指标响应模型"""
    id: int
    timestamp: datetime
    source: str = "mock_data"  # 数据源标识

    class Config:
        from_attributes = True


class IndexSuggestionBase(BaseModel):
    """索引建议基础模型"""
    database_id: int
    table_name: str
    column_names: List[str]
    index_type: str = "btree"
    reason: str
    impact_score: float = 0.0
    estimated_improvement: Optional[str] = None


class IndexSuggestionCreate(IndexSuggestionBase):
    """创建索引建议请求模型"""
    pass


class IndexSuggestionResponse(IndexSuggestionBase):
    """索引建议响应模型"""
    id: int
    status: str
    applied_at: Optional[datetime] = None
    applied_by: Optional[int] = None
    related_query_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    source: str = "mock_data"  # 数据源标识

    @field_validator('column_names', mode='before')
    @classmethod
    def parse_column_names(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @field_validator('related_query_ids', mode='before')
    @classmethod
    def parse_related_query_ids(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    class Config:
        from_attributes = True


class ExecutionPlanBase(BaseModel):
    """执行计划基础模型"""
    database_id: int
    query_text: str
    plan_json: str
    plan_text: str
    cost_estimate: Optional[float] = None
    rows_estimate: Optional[int] = None
    actual_rows: Optional[int] = None
    execution_time: Optional[float] = None


class ExecutionPlanCreate(ExecutionPlanBase):
    """创建执行计划请求模型"""
    pass


class ExecutionPlanResponse(ExecutionPlanBase):
    """执行计划响应模型"""
    id: int
    query_hash: str
    analysis_result: Optional[str] = None
    optimization_suggestions: Optional[str] = None
    timestamp: datetime
    source: str = "mock_data"  # 数据源标识

    class Config:
        from_attributes = True


class TuningTaskBase(BaseModel):
    """调优任务基础模型"""
    database_id: int
    task_type: str  # index_creation, query_rewrite, config_tuning
    task_name: str
    description: Optional[str] = None
    task_config: Dict[str, Any]
    execution_sql: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)


class TuningTaskCreate(TuningTaskBase):
    """创建调优任务请求模型"""
    pass


class TuningTaskResponse(TuningTaskBase):
    """调优任务响应模型"""
    id: int
    status: str
    execution_result: Optional[str] = None
    error_message: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    related_suggestion_id: Optional[int] = None
    created_at: datetime
    source: str = "mock_data"  # 数据源标识

    @field_validator('task_config', mode='before')
    @classmethod
    def parse_task_config(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    class Config:
        from_attributes = True


class SystemDiagnosisBase(BaseModel):
    """系统诊断基础模型"""
    database_id: int
    diagnosis_type: str = "full"  # full, quick, specific


class SystemDiagnosisCreate(SystemDiagnosisBase):
    """创建系统诊断请求模型"""
    pass


class SystemDiagnosisResponse(SystemDiagnosisBase):
    """系统诊断响应模型"""
    id: int
    overall_score: float
    diagnosis_result: str
    recommendations: Optional[str] = None
    performance_score: float
    security_score: float
    maintenance_score: float
    timestamp: datetime
    source: str = "mock_data"  # 数据源标识

    class Config:
        from_attributes = True


class PerformanceDashboardResponse(BaseModel):
    """性能监控仪表板响应模型"""
    current_stats: Dict[str, Any]
    time_series_data: Dict[str, List[Dict[str, Any]]]
    alerts: List[Dict[str, Any]]
    system_health_score: float


class QueryAnalysisRequest(BaseModel):
    """查询分析请求模型"""
    query_text: str
    execution_time: Optional[float] = None
    rows_examined: Optional[int] = None


class QueryAnalysisResponse(BaseModel):
    """查询分析响应模型"""
    query_complexity_score: float
    efficiency_score: float
    suggestions: List[Dict[str, Any]]
    priority_score: float
    optimization_recommendations: List[str]


class OptimizationSuggestion(BaseModel):
    """优化建议模型"""
    type: str
    description: str
    impact: str  # high, medium, low
    estimated_improvement: str
    implementation_steps: List[str]


class TaskExecutionRequest(BaseModel):
    """任务执行请求模型"""
    task_id: int


class TaskExecutionResponse(BaseModel):
    """任务执行响应模型"""
    success: bool
    message: str
    execution_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class PerformanceStatisticsResponse(BaseModel):
    """性能统计响应模型"""
    period: str
    total_queries: int
    slow_queries: int
    slow_query_percentage: float
    avg_execution_time: float
    max_execution_time: float
    queries_per_second: float
    trend: str  # improving, stable, worsening


class CreateIndexTaskRequest(BaseModel):
    """创建索引任务请求体（前端JSON）。"""
    table_name: str
    column_names: List[str]
    index_type: Optional[str] = "btree"
    reason: str


class QueryPatternAnalysisResponse(BaseModel):
    """查询模式分析响应模型"""
    total_slow_queries: int
    avg_execution_time: float
    most_common_patterns: List[Dict[str, Any]]
    top_tables: List[Dict[str, Any]]
    recommendations: List[str]


class IndexOptimizationPlan(BaseModel):
    """索引优化计划模型"""
    table_name: str
    existing_indexes: List[Dict[str, Any]]
    recommended_indexes: List[Dict[str, Any]]
    redundant_indexes: List[Dict[str, Any]]
    impact_assessment: Dict[str, Any]
    implementation_priority: str


class SystemBottleneckAnalysis(BaseModel):
    """系统瓶颈分析模型"""
    bottleneck_type: str  # cpu, memory, io, network
    severity: str  # critical, high, medium, low
    description: str
    current_value: Any
    threshold_value: Any
    recommendations: List[str]
    estimated_improvement: str
