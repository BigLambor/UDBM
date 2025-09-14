"""
数据库相关的数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DatabaseTypeResponse(BaseModel):
    """数据库类型响应模型"""
    id: int
    name: str
    display_name: str
    driver_class: Optional[str]
    default_port: Optional[int]
    supported_features: Dict[str, Any] = Field(default_factory=dict)
    config_template: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DatabaseInstanceBase(BaseModel):
    """数据库实例基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    type_id: int
    host: str = Field(..., max_length=100)
    port: int = Field(..., ge=1, le=65535)
    database_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    environment: str = Field(default="production", pattern="^(development|staging|production)$")
    status: str = Field(default="active", pattern="^(active|inactive|maintenance|error)$")


class DatabaseInstanceCreate(DatabaseInstanceBase):
    """创建数据库实例请求模型"""
    password_encrypted: Optional[str] = None
    health_status: str = Field(default="unknown", pattern="^(healthy|warning|critical|unknown)$")


class DatabaseInstanceUpdate(BaseModel):
    """更新数据库实例请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, max_length=100)
    port: Optional[int] = Field(None, ge=1, le=65535)
    database_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    password_encrypted: Optional[str] = None
    environment: Optional[str] = Field(None, pattern="^(development|staging|production)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive|maintenance|error)$")
    health_status: Optional[str] = Field(None, pattern="^(healthy|warning|critical|unknown)$")


class DatabaseInstanceResponse(DatabaseInstanceBase):
    """数据库实例响应模型"""
    id: int
    type: str  # 数据库类型名称，如 'postgresql', 'mysql' 等
    password_encrypted: Optional[str] = None
    health_status: str
    last_health_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatabaseTestConnectionRequest(BaseModel):
    """数据库连接测试请求模型"""
    timeout: int = Field(default=30, ge=5, le=300)


class DatabaseTestConnectionResponse(BaseModel):
    """数据库连接测试响应模型"""
    database_id: int
    success: bool
    message: str
    response_time: float
    error_details: Optional[str] = None
    database_info: Optional[Dict[str, Any]] = None


class DatabaseGroupBase(BaseModel):
    """数据库分组基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DatabaseGroupCreate(DatabaseGroupBase):
    """创建数据库分组请求模型"""
    pass


class DatabaseGroupResponse(DatabaseGroupBase):
    """数据库分组响应模型"""
    id: int
    level: int
    path: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatabaseGroupMemberAdd(BaseModel):
    """添加数据库到分组请求模型"""
    database_ids: list[int] = Field(..., min_items=1)


class DatabaseGroupMemberResponse(BaseModel):
    """分组成员响应模型"""
    id: int
    group_id: int
    database_id: int
    added_at: datetime

    class Config:
        from_attributes = True
