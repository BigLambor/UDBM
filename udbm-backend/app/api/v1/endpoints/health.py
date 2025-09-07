"""
健康检查API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "service": "UDBM API",
        "version": "1.0.0"
    }


@router.get("/database")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """数据库连接健康检查"""
    try:
        # 执行简单的数据库查询
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
        return {
            "status": "healthy",
            "database": "connected",
            "message": "Database connection is healthy"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """详细健康检查"""
    health_status = {
        "service": "UDBM API",
        "version": "1.0.0",
        "status": "healthy",
        "checks": {}
    }

    # 检查数据库连接
    try:
        result = await db.execute(text("SELECT version()"))
        version = await result.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "version": version[0] if version else "unknown"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    return health_status
