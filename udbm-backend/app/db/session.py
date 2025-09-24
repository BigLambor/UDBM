"""
数据库会话管理
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建异步引擎
import os
if "sqlite" in settings.get_database_uri:
    # SQLite doesn't support these pool settings
    engine = create_async_engine(
        settings.get_database_uri,
        echo=True,  # 开发环境显示SQL语句
        connect_args={"check_same_thread": False} if "sqlite" in settings.get_database_uri else {}
    )
else:
    engine = create_async_engine(
        settings.get_database_uri,
        pool_size=settings.SQLALCHEMY_POOL_SIZE,
        max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
        pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
        pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
        echo=True,  # 开发环境显示SQL语句
    )

# 创建异步会话工厂
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# 基础数据库会话
async def get_db_session() -> AsyncSession:
    """
    获取数据库会话（用于非依赖注入场景）
    """
    async with async_session_factory() as session:
        return session
