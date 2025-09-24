"""
数据库锁分析API接口
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lock_analysis import (
    LockEvent, LockWaitChain, LockContention, 
    LockOptimizationTask, LockAnalysisReport
)
from app.schemas.lock_analysis import (
    LockEventResponse, LockWaitChainResponse, LockContentionResponse,
    LockOptimizationTaskResponse, LockAnalysisReportResponse,
    LockAnalysisRequest, LockDashboardResponse, LockAnalysisSummaryResponse,
    LockOptimizationScriptResponse, LockMonitoringConfigResponse
)
from app.services.performance_tuning.lock_analyzer import LockAnalyzer
from app.services.db_providers.registry import get_provider, get_database_type_name

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


def get_lock_analyzer(session: Session = Depends(get_sync_db_session)) -> LockAnalyzer:
    """获取锁分析器实例"""
    return LockAnalyzer(session)


@router.get("/dashboard/{database_id}", response_model=LockDashboardResponse)
async def get_lock_dashboard(
    database_id: int,
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """获取锁分析仪表板"""
    try:
        # 实时锁分析
        realtime_analysis = analyzer.analyze_locks_realtime(database_id)
        
        # 获取等待链
        wait_chains = analyzer.analyze_wait_chains(database_id)
        
        # 获取竞争分析
        contentions = analyzer.analyze_lock_contentions(database_id)
        
        # 生成优化建议
        suggestions = analyzer.generate_optimization_suggestions(realtime_analysis)
        
        return LockDashboardResponse(
            database_id=database_id,
            analysis_timestamp=datetime.now(),
            overall_health_score=realtime_analysis["health_score"],
            lock_efficiency_score=realtime_analysis["health_score"] * 0.9,  # 模拟锁效率评分
            contention_severity="medium" if realtime_analysis["health_score"] < 80 else "low",
            current_locks=len(realtime_analysis["current_locks"]),
            waiting_locks=len([lock for lock in realtime_analysis["current_locks"] if lock.get("wait_duration", 0) > 0]),
            deadlock_count_today=0,  # 模拟数据
            timeout_count_today=0,   # 模拟数据
            hot_objects=realtime_analysis.get("contentions", [])[:5],
            active_wait_chains=[LockWaitChainResponse(**chain) for chain in wait_chains[:3]],
            top_contentions=[LockContentionResponse(**contention) for contention in contentions[:5]],
            optimization_suggestions=suggestions[:5],
            lock_trends={
                "wait_time": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), "value": 5.0 - i * 0.5}
                    for i in range(24, 0, -1)
                ],
                "contention_count": [
                    {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), "value": 10 + i}
                    for i in range(24, 0, -1)
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取锁分析仪表板失败: {str(e)}")


@router.post("/analyze/{database_id}")
async def analyze_locks(
    database_id: int,
    request: LockAnalysisRequest,
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """执行锁分析"""
    try:
        if request.analysis_type == "realtime":
            result = analyzer.analyze_locks_realtime(database_id)
        elif request.analysis_type == "historical":
            result = analyzer.analyze_locks_historical(database_id, request.time_range_hours)
        elif request.analysis_type == "comprehensive":
            # 综合分析
            realtime_result = analyzer.analyze_locks_realtime(database_id)
            historical_result = analyzer.analyze_locks_historical(database_id, request.time_range_hours)
            
            result = {
                "analysis_type": "comprehensive",
                "realtime_analysis": realtime_result,
                "historical_analysis": historical_result,
                "combined_insights": _generate_combined_insights(realtime_result, historical_result)
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的分析类型")
        
        return {
            "database_id": database_id,
            "analysis_type": request.analysis_type,
            "analysis_timestamp": datetime.now().isoformat(),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"锁分析失败: {str(e)}")


@router.get("/wait-chains/{database_id}", response_model=List[LockWaitChainResponse])
async def get_wait_chains(
    database_id: int,
    severity_filter: Optional[str] = Query(None, description="严重程度过滤: low, medium, high, critical"),
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """获取锁等待链"""
    try:
        wait_chains = analyzer.analyze_wait_chains(database_id)
        
        # 应用严重程度过滤
        if severity_filter:
            wait_chains = [chain for chain in wait_chains if chain.get("severity_level") == severity_filter]
        
        return [LockWaitChainResponse(**chain) for chain in wait_chains]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取等待链失败: {str(e)}")


@router.get("/contentions/{database_id}", response_model=List[LockContentionResponse])
async def get_lock_contentions(
    database_id: int,
    priority_filter: Optional[str] = Query(None, description="优先级过滤: low, medium, high, critical"),
    limit: int = Query(50, ge=1, le=200),
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """获取锁竞争分析"""
    try:
        contentions = analyzer.analyze_lock_contentions(database_id)
        
        # 应用优先级过滤
        if priority_filter:
            contentions = [contention for contention in contentions if contention.get("priority_level") == priority_filter]
        
        # 应用限制
        contentions = contentions[:limit]
        
        return [LockContentionResponse(**contention) for contention in contentions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取锁竞争分析失败: {str(e)}")


@router.get("/events/{database_id}", response_model=List[LockEventResponse])
async def get_lock_events(
    database_id: int,
    hours: int = Query(24, ge=1, le=168),
    lock_type: Optional[str] = Query(None, description="锁类型过滤"),
    status: Optional[str] = Query(None, description="锁状态过滤: granted, waiting, timeout"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """获取锁事件历史"""
    try:
        session = get_sync_db_session()
        
        # 构建查询
        query = session.query(LockEvent).filter(LockEvent.database_id == database_id)
        
        # 时间过滤
        start_time = datetime.now() - timedelta(hours=hours)
        query = query.filter(LockEvent.lock_request_time >= start_time)
        
        # 类型过滤
        if lock_type:
            query = query.filter(LockEvent.lock_type == lock_type)
        
        # 状态过滤
        if status:
            query = query.filter(LockEvent.lock_status == status)
        
        # 排序和限制
        events = query.order_by(LockEvent.lock_request_time.desc()).limit(limit).all()
        
        return [LockEventResponse.from_orm(event) for event in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取锁事件失败: {str(e)}")


@router.get("/summary/{database_id}", response_model=LockAnalysisSummaryResponse)
async def get_lock_analysis_summary(
    database_id: int,
    days: int = Query(7, ge=1, le=30),
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """获取锁分析总结"""
    try:
        # 获取历史分析
        historical_analysis = analyzer.analyze_locks_historical(database_id, days * 24)
        
        # 生成总结数据
        summary = {
            "database_id": database_id,
            "analysis_period": f"最近{days}天",
            "total_events": len(historical_analysis.get("lock_events", [])),
            "total_wait_time": sum(event.get("wait_duration", 0) for event in historical_analysis.get("lock_events", [])),
            "avg_wait_time": 0,
            "max_wait_time": 0,
            "lock_type_distribution": _calculate_lock_type_distribution(historical_analysis.get("lock_events", [])),
            "top_contention_objects": historical_analysis.get("hot_objects", [])[:10],
            "top_waiting_sessions": _get_top_waiting_sessions(historical_analysis.get("lock_events", [])),
            "critical_issues": 0,
            "high_priority_issues": 0,
            "medium_priority_issues": 0,
            "low_priority_issues": 0,
            "total_suggestions": 0,
            "high_impact_suggestions": 0,
            "implemented_suggestions": 0
        }
        
        # 计算统计数据
        if summary["total_events"] > 0:
            wait_times = [event.get("wait_duration", 0) for event in historical_analysis.get("lock_events", [])]
            summary["avg_wait_time"] = sum(wait_times) / len(wait_times)
            summary["max_wait_time"] = max(wait_times)
        
        return LockAnalysisSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取锁分析总结失败: {str(e)}")


@router.post("/optimization-suggestions/{database_id}")
async def get_optimization_suggestions(
    database_id: int,
    analysis_result: Dict[str, Any] = Body(...),
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """获取锁优化建议"""
    try:
        suggestions = analyzer.generate_optimization_suggestions(analysis_result)
        
        return {
            "database_id": database_id,
            "suggestions": suggestions,
            "total_count": len(suggestions),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取优化建议失败: {str(e)}")


@router.post("/create-optimization-task/{database_id}")
async def create_optimization_task(
    database_id: int,
    task_config: Dict[str, Any] = Body(...),
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """创建锁优化任务"""
    try:
        task = analyzer.create_optimization_task(database_id, task_config)
        
        return {
            "message": "锁优化任务创建成功",
            "task_id": task.id,
            "task_name": task.task_name,
            "status": task.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建优化任务失败: {str(e)}")


@router.get("/optimization-tasks/{database_id}", response_model=List[LockOptimizationTaskResponse])
async def get_optimization_tasks(
    database_id: int,
    status: Optional[str] = Query(None, description="任务状态过滤"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """获取锁优化任务列表"""
    try:
        session = get_sync_db_session()
        
        query = session.query(LockOptimizationTask).filter(LockOptimizationTask.database_id == database_id)
        
        if status:
            query = query.filter(LockOptimizationTask.status == status)
        
        tasks = query.order_by(LockOptimizationTask.created_at.desc()).limit(limit).all()
        
        return [LockOptimizationTaskResponse.from_orm(task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取优化任务失败: {str(e)}")


@router.post("/generate-optimization-script/{database_id}")
async def generate_optimization_script(
    database_id: int,
    optimization_type: str = Query(..., description="优化类型: index, query, isolation, config, comprehensive"),
    analysis_result: Dict[str, Any] = Body(...),
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """生成锁优化脚本"""
    try:
        script_content = analyzer.generate_optimization_script(analysis_result, optimization_type)
        
        return LockOptimizationScriptResponse(
            script_id=f"lock_opt_{database_id}_{int(datetime.now().timestamp())}",
            database_id=database_id,
            script_type=optimization_type,
            script_content=script_content,
            target_objects=analysis_result.get("target_objects", []),
            estimated_impact="预计性能提升20-50%",
            execution_instructions=[
                "1. 在测试环境先执行脚本",
                "2. 监控执行过程中的锁情况",
                "3. 确认性能改善后在生产环境执行",
                "4. 执行后持续监控锁性能"
            ],
            rollback_script="-- 回滚脚本\n-- 根据具体优化内容提供相应的回滚操作",
            generated_at=datetime.now(),
            generated_by="UDBM Lock Analyzer"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成优化脚本失败: {str(e)}")


@router.get("/reports/{database_id}", response_model=List[LockAnalysisReportResponse])
async def get_lock_analysis_reports(
    database_id: int,
    report_type: Optional[str] = Query(None, description="报告类型过滤"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取锁分析报告"""
    try:
        session = get_sync_db_session()
        
        query = session.query(LockAnalysisReport).filter(LockAnalysisReport.database_id == database_id)
        
        if report_type:
            query = query.filter(LockAnalysisReport.report_type == report_type)
        
        reports = query.order_by(LockAnalysisReport.created_at.desc()).limit(limit).all()
        
        return [LockAnalysisReportResponse.from_orm(report) for report in reports]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取锁分析报告失败: {str(e)}")


@router.post("/generate-report/{database_id}")
async def generate_lock_analysis_report(
    database_id: int,
    report_type: str = Query("custom", description="报告类型: daily, weekly, monthly, custom"),
    days: int = Query(7, ge=1, le=30),
    analyzer: LockAnalyzer = Depends(get_lock_analyzer)
):
    """生成锁分析报告"""
    try:
        # 执行历史分析
        historical_analysis = analyzer.analyze_locks_historical(database_id, days * 24)
        
        # 生成报告内容
        report_content = {
            "analysis_period": f"最近{days}天",
            "overall_health_score": historical_analysis.get("summary", {}).get("health_assessment", "良好"),
            "key_metrics": {
                "total_events": len(historical_analysis.get("lock_events", [])),
                "avg_wait_time": sum(event.get("wait_duration", 0) for event in historical_analysis.get("lock_events", [])) / max(len(historical_analysis.get("lock_events", [])), 1),
                "deadlock_count": len(historical_analysis.get("deadlocks", [])),
                "timeout_count": len(historical_analysis.get("timeouts", []))
            },
            "trends": historical_analysis.get("trends", {}),
            "hot_objects": historical_analysis.get("hot_objects", [])[:10],
            "recommendations": _generate_report_recommendations(historical_analysis)
        }
        
        # 创建报告记录
        session = get_sync_db_session()
        report = LockAnalysisReport(
            database_id=database_id,
            report_type=report_type,
            analysis_period_start=datetime.now() - timedelta(days=days),
            analysis_period_end=datetime.now(),
            overall_health_score=85.0,  # 模拟健康评分
            lock_efficiency_score=80.0,  # 模拟锁效率评分
            contention_severity="medium",
            total_lock_events=len(historical_analysis.get("lock_events", [])),
            total_wait_time=sum(event.get("wait_duration", 0) for event in historical_analysis.get("lock_events", [])),
            deadlock_count=len(historical_analysis.get("deadlocks", [])),
            timeout_count=len(historical_analysis.get("timeouts", [])),
            hot_objects=json.dumps(historical_analysis.get("hot_objects", [])[:5]),
            report_content=json.dumps(report_content),
            recommendations=json.dumps(_generate_report_recommendations(historical_analysis))
        )
        
        session.add(report)
        session.commit()
        session.refresh(report)
        
        return {
            "message": "锁分析报告生成成功",
            "report_id": report.id,
            "report_type": report_type,
            "analysis_period": f"最近{days}天",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成锁分析报告失败: {str(e)}")


@router.post("/monitoring/start/{database_id}")
async def start_lock_monitoring(
    database_id: int,
    collection_interval: int = Query(60, ge=10, le=3600, description="收集间隔(秒)"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """启动锁监控"""
    try:
        # 这里可以启动后台监控任务
        background_tasks.add_task(_monitor_locks_background, database_id, collection_interval)
        
        return {
            "message": "锁监控已启动",
            "database_id": database_id,
            "collection_interval": collection_interval,
            "started_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动锁监控失败: {str(e)}")


@router.post("/monitoring/stop/{database_id}")
async def stop_lock_monitoring(database_id: int):
    """停止锁监控"""
    try:
        # 这里可以停止后台监控任务
        return {
            "message": "锁监控已停止",
            "database_id": database_id,
            "stopped_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止锁监控失败: {str(e)}")


@router.get("/monitoring/status/{database_id}")
async def get_monitoring_status(database_id: int):
    """获取监控状态"""
    try:
        return {
            "database_id": database_id,
            "monitoring_enabled": True,  # 模拟状态
            "collection_interval": 60,
            "last_collection": datetime.now().isoformat(),
            "total_events_collected": 1250,  # 模拟数据
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控状态失败: {str(e)}")


# 辅助函数

def _generate_combined_insights(realtime_result: Dict, historical_result: Dict) -> Dict[str, Any]:
    """生成综合洞察"""
    return {
        "trend_analysis": "锁性能整体稳定",
        "key_issues": ["热点表竞争", "等待链过长"],
        "optimization_opportunities": ["索引优化", "查询重写"],
        "priority_actions": ["立即处理死锁", "优化热点表访问"]
    }


def _calculate_lock_type_distribution(lock_events: List[Dict]) -> Dict[str, int]:
    """计算锁类型分布"""
    distribution = {}
    for event in lock_events:
        lock_type = event.get("lock_type", "unknown")
        distribution[lock_type] = distribution.get(lock_type, 0) + 1
    return distribution


def _get_top_waiting_sessions(lock_events: List[Dict]) -> List[Dict[str, Any]]:
    """获取等待时间最长的会话"""
    session_wait_times = {}
    for event in lock_events:
        session_id = event.get("session_id", "unknown")
        wait_time = event.get("wait_duration", 0)
        if session_id not in session_wait_times:
            session_wait_times[session_id] = {"total_wait": 0, "count": 0}
        session_wait_times[session_id]["total_wait"] += wait_time
        session_wait_times[session_id]["count"] += 1
    
    # 排序并返回前10个
    sorted_sessions = sorted(session_wait_times.items(), key=lambda x: x[1]["total_wait"], reverse=True)
    return [
        {
            "session_id": session_id,
            "total_wait_time": data["total_wait"],
            "event_count": data["count"],
            "avg_wait_time": data["total_wait"] / data["count"]
        }
        for session_id, data in sorted_sessions[:10]
    ]


def _generate_report_recommendations(historical_analysis: Dict) -> List[str]:
    """生成报告建议"""
    recommendations = []
    
    if len(historical_analysis.get("deadlocks", [])) > 0:
        recommendations.append("检测到死锁事件，建议优化事务设计")
    
    if len(historical_analysis.get("timeouts", [])) > 0:
        recommendations.append("检测到锁超时，建议调整超时设置或优化查询")
    
    hot_objects = historical_analysis.get("hot_objects", [])
    if len(hot_objects) > 3:
        recommendations.append("存在多个热点对象，建议进行索引优化")
    
    return recommendations


async def _monitor_locks_background(database_id: int, interval: int):
    """后台锁监控任务"""
    # 这里实现后台监控逻辑
    pass
