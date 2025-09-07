"""
数据库基础模型定义
"""
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer
from datetime import datetime


class Base(AsyncAttrs, DeclarativeBase):
    """
    SQLAlchemy基础模型类
    """
    pass


# 基础字段混入类
class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class UserMixin:
    """用户相关混入类"""
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("udbm.users.id"), nullable=True)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey("udbm.users.id"), nullable=True)
