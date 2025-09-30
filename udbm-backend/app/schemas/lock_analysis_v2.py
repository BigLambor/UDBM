"""
锁分析 V2 Schema定义

优化后的API响应结构，支持：
- 结构化元数据
- 标准化指标格式
- 趋势数据支持
- 告警信息结构化
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


# ==================== 元数据 ====================

class TimeRange(BaseModel):
    """时间范围"""
    start: datetime
    end: datetime
    duration: str  # "5m", "1h", "24h" etc.


class DashboardMeta(BaseModel):
    """仪表板元数据"""
    database_id: int
    database_type: str
    collection_timestamp: datetime
    analysis_timestamp: datetime
    time_range: TimeRange
    data_source: str = "v2"
    is_live: bool = False
    cache_hit: bool = False
    duration_ms: int


# ==================== 指标值 ====================

class MetricValue(BaseModel):
    """指标值"""
    value: Union[int, float, str]
    unit: Optional[str] = None
    status: str = "normal"  # normal/warning/critical/good
    threshold: Optional[float] = None
    change_percent: Optional[float] = None
    previous_value: Optional[Union[int, float]] = None


# ==================== 趋势数据 ====================

class TrendPoint(BaseModel):
    """趋势数据点"""
    timestamp: datetime
    value: float
    label: Optional[str] = None


# ==================== 告警 ====================

class Action(BaseModel):
    """可执行操作"""
    id: str
    label: str
    type: str  # navigate/api_call/external_link
    payload: Dict[str, Any] = {}


class Alert(BaseModel):
    """告警信息"""
    id: str
    severity: str  # critical/high/medium/low
    type: str  # deadlock/timeout/high_wait/contention/health
    title: str
    message: str
    timestamp: datetime
    affected_objects: List[str] = []
    recommended_actions: List[Action] = []


# ==================== 详细数据 ====================

class ContentionObject(BaseModel):
    """竞争对象"""
    object_name: str
    contention_count: int
    total_wait_time: float
    avg_wait_time: float
    max_wait_time: float
    priority: str
    affected_sessions: Optional[int] = None


class WaitChainSummary(BaseModel):
    """等待链摘要"""
    chain_id: str
    chain_length: int
    total_wait_time: float
    severity: str
    head_session: str
    tail_session: str
    is_cycle: Optional[bool] = False


class OptimizationAdviceSummary(BaseModel):
    """优化建议摘要"""
    advice_id: str
    type: str
    priority: str
    title: str
    description: str
    object_name: Optional[str] = None
    impact_score: float
    estimated_improvement: str
    actions: List[str] = []


class DashboardDetails(BaseModel):
    """详细数据"""
    hot_objects: List[ContentionObject] = []
    active_wait_chains: List[WaitChainSummary] = []
    top_recommendations: List[OptimizationAdviceSummary] = []
    lock_type_distribution: Dict[str, int] = {}


# ==================== 主响应 ====================

class LockDashboardResponseV2(BaseModel):
    """锁分析仪表板响应 V2"""
    meta: DashboardMeta
    metrics: Dict[str, MetricValue]
    trends: Dict[str, List[TrendPoint]]
    alerts: List[Alert]
    details: DashboardDetails
    
    class Config:
        json_schema_extra = {
            "example": {
                "meta": {
                    "database_id": 1,
                    "database_type": "mysql",
                    "collection_timestamp": "2024-01-15T10:30:00Z",
                    "analysis_timestamp": "2024-01-15T10:30:05Z",
                    "time_range": {
                        "start": "2024-01-15T09:30:00Z",
                        "end": "2024-01-15T10:30:00Z",
                        "duration": "1h"
                    },
                    "data_source": "v2",
                    "is_live": True,
                    "cache_hit": False,
                    "duration_ms": 234
                },
                "metrics": {
                    "health_score": {
                        "value": 85.5,
                        "unit": "/100",
                        "status": "good",
                        "threshold": 80.0,
                        "change_percent": 2.3
                    }
                },
                "trends": {},
                "alerts": [],
                "details": {
                    "hot_objects": [],
                    "active_wait_chains": [],
                    "top_recommendations": []
                }
            }
        }
