"""
API v1 路由定义
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    databases, health, performance_tuning, lock_analysis
)

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(databases.router, prefix="/databases", tags=["databases"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(performance_tuning.router, prefix="/performance", tags=["performance-tuning"])
api_router.include_router(lock_analysis.router, prefix="/performance-tuning/lock-analysis", tags=["lock-analysis"])
