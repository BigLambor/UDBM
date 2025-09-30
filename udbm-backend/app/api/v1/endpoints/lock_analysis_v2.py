"""
数据库锁分析API接口 - V2版本

集成重构后的新架构
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.database import DatabaseInstance
from app.schemas.lock_analysis import (
    LockAnalysisRequest, LockDashboardResponse, LockAnalysisSummaryResponse
)

# 导入新架构组件
from app.services.lock_analysis import (
    LockAnalysisOrchestrator,
    LockAnalysisCache,
    CollectorRegistry
)
from app.services.lock_analysis.connection_manager import ConnectionPoolManager
from app.services.lock_analysis.adapters import DashboardResponseAdapter

logger = logging.getLogger(__name__)

router = APIRouter()


def get_sync_db_session() -> Session:
    """获取同步数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    sync_engine = create_engine(
        settings.get_database_uri.replace('postgresql+asyncpg://', 'postgresql://'),
        echo=False
    )
    sync_session_factory = sessionmaker(bind=sync_engine)
    return sync_session_factory()


# 全局缓存实例
_cache_instance = None

def get_cache() -> LockAnalysisCache:
    """获取缓存实例（单例）"""
    global _cache_instance
    if _cache_instance is None:
        try:
            # 尝试使用Redis
            _cache_instance = LockAnalysisCache(
                redis_url='redis://localhost:6379/0',
                enable_local=True,
                enable_redis=True
            )
            logger.info("Cache initialized with Redis")
        except:
            # 降级为只使用本地缓存
            _cache_instance = LockAnalysisCache(
                enable_local=True,
                enable_redis=False
            )
            logger.warning("Cache initialized with local cache only (Redis unavailable)")
    
    return _cache_instance


async def get_orchestrator(database_id: int) -> Optional[LockAnalysisOrchestrator]:
    """
    获取锁分析编排器
    
    Args:
        database_id: 数据库ID
        
    Returns:
        LockAnalysisOrchestrator: 分析编排器实例
    """
    try:
        # 获取数据库信息
        session = get_sync_db_session()
        database = session.query(DatabaseInstance).filter(
            DatabaseInstance.id == database_id
        ).first()
        
        if not database:
            logger.error(f"Database {database_id} not found")
            return None
        
        # 获取数据库类型名称
        from app.models.database import DatabaseType
        db_type_obj = session.query(DatabaseType).filter(DatabaseType.id == database.type_id).first()
        db_type = db_type_obj.name.lower() if db_type_obj else "unknown"
        
        # 检查是否支持
        supported_types = CollectorRegistry.list_supported_types()
        if db_type not in supported_types:
            logger.error(f"Database type {db_type} not supported")
            return None
        
        # 获取或创建连接池
        pool = await ConnectionPoolManager.get_pool(
            database_id=database_id,
            db_type=db_type,
            host=database.host,
            port=database.port,
            database=database.database_name,
            username=database.username,
            password=database.password_encrypted,  # 注意：实际应该解密
            min_size=2,
            max_size=10
        )
        
        if not pool:
            logger.error(f"Failed to create connection pool for database {database_id}")
            return None
        
        # 创建采集器
        collector = CollectorRegistry.create_collector(
            db_type,
            pool=pool,
            database_id=database_id
        )
        
        if not collector:
            logger.error(f"Failed to create collector for database {database_id}")
            return None
        
        # 获取缓存
        cache = get_cache()
        
        # 创建编排器
        orchestrator = LockAnalysisOrchestrator(
            collector=collector,
            cache=cache
        )
        
        logger.info(f"Created orchestrator for database {database_id} ({db_type})")
        
        return orchestrator
        
    except Exception as e:
        logger.error(f"Failed to get orchestrator: {e}", exc_info=True)
        return None


@router.get("/dashboard/{database_id}")
async def get_lock_dashboard_v2(
    database_id: int,
    force_refresh: bool = Query(False, description="强制刷新，跳过缓存")
):
    """
    获取锁分析仪表板 - V2版本
    
    使用新架构的真实数据采集和智能分析
    """
    try:
        logger.info(f"Dashboard request for database {database_id}, force_refresh={force_refresh}")
        
        # 获取编排器
        orchestrator = await get_orchestrator(database_id)
        
        if not orchestrator:
            # 降级为旧版API
            logger.warning(f"Orchestrator not available, falling back to old API")
            
            # 导入旧版实现
            from app.services.performance_tuning.lock_analyzer_providers import get_lock_analyzer_by_type
            
            session = get_sync_db_session()
            database = session.query(DatabaseInstance).filter(
                DatabaseInstance.id == database_id
            ).first()
            
            if not database:
                raise HTTPException(status_code=404, detail="数据库不存在")
            
            # 获取数据库类型名称
            from app.models.database import DatabaseType
            db_type_obj = session.query(DatabaseType).filter(DatabaseType.id == database.type_id).first()
            db_type = db_type_obj.name.lower() if db_type_obj else "unknown"
            
            lock_analyzer_class = get_lock_analyzer_by_type(db_type)
            mock_data = lock_analyzer_class.get_mock_data(database_id)
            
            if "error" in mock_data and mock_data["error"] == "unsupported":
                raise HTTPException(
                    status_code=404,
                    detail=f"{db_type.upper()} 数据库暂不支持锁分析功能"
                )
            
            return mock_data
        
        # 使用新架构执行分析
        analysis_result = await orchestrator.analyze_comprehensive(
            database_id=database_id,
            force_refresh=force_refresh,
            duration=timedelta(hours=1)
        )
        
        # 获取数据库类型
        session = get_sync_db_session()
        database = session.query(DatabaseInstance).filter(
            DatabaseInstance.id == database_id
        ).first()
        
        # 获取数据库类型名称
        from app.models.database import DatabaseType
        if database:
            db_type_obj = session.query(DatabaseType).filter(DatabaseType.id == database.type_id).first()
            db_type = db_type_obj.name.lower() if db_type_obj else "postgresql"
        else:
            db_type = "postgresql"
        
        # 转换为前端期望格式
        dashboard_data = DashboardResponseAdapter.adapt(
            analysis_result,
            db_type=db_type
        )
        
        logger.info(
            f"Dashboard generated for database {database_id}, "
            f"health_score={analysis_result.health_score:.2f}"
        )
        
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取锁分析仪表板失败: {str(e)}"
        )


@router.post("/analyze/{database_id}")
async def analyze_locks_v2(
    database_id: int,
    request: LockAnalysisRequest
):
    """
    执行锁分析 - V2版本
    """
    try:
        logger.info(
            f"Analysis request for database {database_id}, "
            f"type={request.analysis_type}"
        )
        
        # 获取编排器
        orchestrator = await get_orchestrator(database_id)
        
        if not orchestrator:
            raise HTTPException(
                status_code=503,
                detail="无法连接到目标数据库"
            )
        
        # 根据分析类型执行不同的分析
        if request.analysis_type == "realtime":
            # 实时快速分析
            result = await orchestrator.analyze_realtime(database_id)
            
        elif request.analysis_type == "comprehensive":
            # 综合分析
            analysis_result = await orchestrator.analyze_comprehensive(
                database_id=database_id,
                duration=timedelta(hours=request.time_range_hours)
            )
            
            result = {
                "health_score": analysis_result.health_score,
                "wait_chains": [c.to_dict() for c in analysis_result.wait_chains],
                "contentions": [c.to_dict() for c in analysis_result.contentions],
                "statistics": analysis_result.statistics.to_dict(),
                "recommendations": [r.to_dict() for r in analysis_result.recommendations]
            }
        else:
            # 默认执行综合分析
            analysis_result = await orchestrator.analyze_comprehensive(
                database_id=database_id
            )
            result = analysis_result.to_dict()
        
        return {
            "database_id": database_id,
            "analysis_type": request.analysis_type,
            "analysis_timestamp": datetime.now().isoformat(),
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"锁分析失败: {str(e)}"
        )


@router.get("/health-check/{database_id}")
async def health_check(database_id: int):
    """
    健康检查 - 检查分析服务是否正常
    """
    try:
        orchestrator = await get_orchestrator(database_id)
        
        if not orchestrator:
            return {
                "database_id": database_id,
                "healthy": False,
                "message": "无法创建分析器"
            }
        
        is_healthy = await orchestrator.health_check()
        
        return {
            "database_id": database_id,
            "healthy": is_healthy,
            "message": "正常" if is_healthy else "连接失败",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "database_id": database_id,
            "healthy": False,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/clear-cache/{database_id}")
async def clear_cache(database_id: int):
    """
    清除指定数据库的缓存
    """
    try:
        cache = get_cache()
        pattern = f"lock_analysis:{database_id}:*"
        count = await cache.invalidate_pattern(pattern)
        
        return {
            "database_id": database_id,
            "cleared_count": count,
            "message": f"已清除 {count} 条缓存",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Clear cache failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pool-info")
async def get_pool_info():
    """
    获取所有连接池信息
    """
    try:
        active_pools = ConnectionPoolManager.list_active_pools()
        
        pool_infos = []
        for db_id in active_pools:
            info = ConnectionPoolManager.get_pool_info(db_id)
            if info:
                pool_infos.append({
                    "database_id": db_id,
                    **info,
                    "created_at": info['created_at'].isoformat()
                })
        
        return {
            "total_pools": len(active_pools),
            "pools": pool_infos,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Get pool info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))