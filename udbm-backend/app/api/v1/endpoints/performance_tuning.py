"""
性能调优API接口
"""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.session import get_db

# 临时辅助函数，将异步会话转换为同步会话
def get_db_session(async_session: AsyncSession) -> Session:
    """将AsyncSession转换为同步Session（临时解决方案）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    # 创建同步引擎
    sync_engine = create_engine(
        settings.get_database_uri.replace('postgresql+asyncpg://', 'postgresql://'),
        echo=False
    )
    sync_session_factory = sessionmaker(bind=sync_engine)
    return sync_session_factory()
from app.models.performance_tuning import (
    SlowQuery, PerformanceMetric, IndexSuggestion, ExecutionPlan,
    TuningTask, SystemDiagnosis
)
from app.schemas.performance_tuning import (
    SlowQueryResponse, PerformanceMetricResponse, IndexSuggestionResponse,
    ExecutionPlanResponse, TuningTaskResponse, SystemDiagnosisResponse,
    PerformanceDashboardResponse, QueryAnalysisRequest, QueryAnalysisResponse,
    TaskExecutionRequest, TaskExecutionResponse, PerformanceStatisticsResponse,
    QueryPatternAnalysisResponse
)
from app.services.performance_tuning import (
    SlowQueryAnalyzer, SystemMonitor, TuningExecutor, ExecutionPlanAnalyzer
)
from app.services.performance_tuning.postgres_config_optimizer import PostgreSQLConfigOptimizer
from app.services.db_providers.registry import get_provider

router = APIRouter()


# 依赖注入函数
def get_sync_db_session() -> Session:
    """获取同步数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    # 创建同步引擎
    sync_engine = create_engine(
        settings.get_database_uri.replace('postgresql+asyncpg://', 'postgresql://'),
        echo=False
    )
    sync_session_factory = sessionmaker(bind=sync_engine)
    return sync_session_factory()


def get_slow_query_analyzer(session: Session = Depends(get_sync_db_session)) -> SlowQueryAnalyzer:
    """获取慢查询分析器实例"""
    return SlowQueryAnalyzer(session)


def get_system_monitor(session: Session = Depends(get_sync_db_session)) -> SystemMonitor:
    """获取系统监控器实例"""
    return SystemMonitor(session)


def get_tuning_executor(session: Session = Depends(get_sync_db_session)) -> TuningExecutor:
    """获取调优执行器实例"""
    return TuningExecutor(session)


def get_execution_plan_analyzer(session: Session = Depends(get_sync_db_session)) -> ExecutionPlanAnalyzer:
    """获取执行计划分析器实例"""
    return ExecutionPlanAnalyzer(session)


def get_postgres_config_optimizer(session: Session = Depends(get_sync_db_session)) -> PostgreSQLConfigOptimizer:
    """获取PostgreSQL配置优化器实例"""
    return PostgreSQLConfigOptimizer(session)


@router.get("/dashboard/{database_id}", response_model=PerformanceDashboardResponse)
async def get_performance_dashboard(
    database_id: int,
    hours: int = Query(24, ge=1, le=168),
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """获取性能监控仪表板数据"""
    try:
        # 使用Provider抽象以支持多数据库
        provider = get_provider(get_sync_db_session(), database_id)
        dashboard_data = provider.monitor.dashboard(database_id, hours)
        return PerformanceDashboardResponse(**dashboard_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能仪表板失败: {str(e)}")


@router.get("/slow-queries/{database_id}", response_model=List[SlowQueryResponse])
async def get_slow_queries(
    database_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer)
):
    """获取慢查询列表"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        slow_queries = provider.slow_queries.list(database_id, limit, offset)
        return [SlowQueryResponse.from_orm(query) for query in slow_queries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取慢查询列表失败: {str(e)}")


@router.post("/slow-queries/{database_id}/capture")
async def capture_slow_queries(
    database_id: int,
    threshold_seconds: float = Query(1.0, ge=0.1),
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer),
    db: AsyncSession = Depends(get_db)
):
    """捕获慢查询"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        captured_queries = provider.slow_queries.capture(database_id, threshold_seconds)
        saved_queries = []

        for query_data in captured_queries:
            slow_query = provider.slow_queries.save(query_data)
            saved_queries.append(SlowQueryResponse.from_orm(slow_query))

        return {
            "message": f"成功捕获 {len(saved_queries)} 条慢查询",
            "queries": saved_queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"捕获慢查询失败: {str(e)}")


@router.post("/analyze-query")
async def analyze_query(
    request: QueryAnalysisRequest,
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer)
):
    """分析查询性能"""
    try:
        analysis_result = analyzer.generate_optimization_suggestions(
            request.query_text,
            request.execution_time or 1.0,
            request.rows_examined or 1000
        )

        return QueryAnalysisResponse(
            query_complexity_score=analysis_result["query_analysis"]["complexity_score"],
            efficiency_score=analysis_result["query_analysis"]["efficiency_score"],
            suggestions=analysis_result["suggestions"],
            priority_score=analysis_result["priority_score"],
            optimization_recommendations=[s["description"] for s in analysis_result["suggestions"]]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询分析失败: {str(e)}")


@router.get("/query-patterns/{database_id}", response_model=QueryPatternAnalysisResponse)
async def get_query_patterns(
    database_id: int,
    days: int = Query(7, ge=1, le=90),
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer)
):
    """获取查询模式分析"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        patterns = provider.slow_queries.patterns(database_id, days)
        return QueryPatternAnalysisResponse(**patterns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询模式分析失败: {str(e)}")


@router.get("/statistics/{database_id}", response_model=PerformanceStatisticsResponse)
async def get_performance_statistics(
    database_id: int,
    days: int = Query(7, ge=1, le=90),
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer)
):
    """获取性能统计信息"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        stats = provider.slow_queries.statistics(database_id, days)
        return PerformanceStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")


@router.post("/collect-metrics/{database_id}")
async def collect_performance_metrics(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """收集性能指标"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        metrics = provider.monitor.collect_metrics(database_id)
        saved_metrics = provider.monitor.save_metrics(metrics)

        return {
            "message": f"成功收集 {len(saved_metrics)} 条性能指标",
            "metrics_count": len(saved_metrics)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"收集性能指标失败: {str(e)}")


@router.get("/metrics/{database_id}", response_model=List[PerformanceMetricResponse])
async def get_performance_metrics(
    database_id: int,
    metric_type: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """获取性能指标历史数据"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        if metric_type:
            metrics = provider.monitor.history(database_id, metric_type, hours)
        else:
            metrics = []
            for mtype in ["cpu", "memory", "io", "connections", "throughput"]:
                metrics.extend(provider.monitor.history(database_id, mtype, hours))

        return [PerformanceMetricResponse.from_orm(metric) for metric in metrics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/latest-metrics/{database_id}")
async def get_latest_metrics(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """获取最新性能指标"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        latest_metrics = provider.monitor.latest_metrics(database_id)
        return latest_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新指标失败: {str(e)}")


@router.post("/diagnose/{database_id}", response_model=SystemDiagnosisResponse)
async def perform_system_diagnosis(
    database_id: int,
    diagnosis_type: str = Query("full", regex="^(full|quick|specific)$"),
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """执行系统诊断"""
    try:
        # 与现有实现保持一致，后续可抽象到provider
        diagnosis = monitor.perform_system_diagnosis(database_id)
        return SystemDiagnosisResponse.from_orm(diagnosis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统诊断失败: {str(e)}")


@router.get("/diagnoses/{database_id}", response_model=List[SystemDiagnosisResponse])
async def get_system_diagnoses(
    database_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取系统诊断历史"""
    try:
        session = get_db_session(db)
        diagnoses = session.query(SystemDiagnosis)\
            .filter(SystemDiagnosis.database_id == database_id)\
            .order_by(SystemDiagnosis.timestamp.desc())\
            .limit(limit)\
            .all()

        return [SystemDiagnosisResponse.from_orm(diagnosis) for diagnosis in diagnoses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取诊断历史失败: {str(e)}")


@router.post("/tasks/execute")
async def execute_tuning_task(
    request: TaskExecutionRequest,
    executor: TuningExecutor = Depends(get_tuning_executor)
):
    """执行调优任务"""
    try:
        result = executor.execute_task(request.task_id)
        return TaskExecutionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            execution_details=result,
            error_message=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行调优任务失败: {str(e)}")


@router.get("/tasks/{database_id}", response_model=List[TuningTaskResponse])
async def get_tuning_tasks(
    database_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """获取调优任务列表"""
    try:
        session = get_db_session(db)
        query = session.query(TuningTask)

        if database_id:
            query = query.filter(TuningTask.database_id == database_id)

        if status:
            query = query.filter(TuningTask.status == status)

        tasks = query.order_by(TuningTask.created_at.desc()).limit(limit).all()

        return [TuningTaskResponse.from_orm(task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调优任务失败: {str(e)}")


@router.post("/tasks/{database_id}/create-index")
async def create_index_task(
    database_id: int,
    table_name: str = Query(..., min_length=1),
    column_names: List[str] = Query(..., min_items=1),
    index_type: str = Query("btree"),
    reason: str = Query(...),
    executor: TuningExecutor = Depends(get_tuning_executor)
):
    """创建索引优化任务"""
    try:
        # 查找相关建议
        session = get_db_session(await get_db())
        suggestion = session.query(IndexSuggestion)\
            .filter(
                IndexSuggestion.database_id == database_id,
                IndexSuggestion.table_name == table_name,
                IndexSuggestion.status == "pending"
            )\
            .first()

        if suggestion:
            task = executor.create_index_suggestion_task(suggestion)
        else:
            # 创建新的建议和任务
            suggestion_data = {
                "database_id": database_id,
                "table_name": table_name,
                "column_names": column_names,
                "index_type": index_type,
                "reason": reason,
                "impact_score": 75.0,  # 默认影响评分
                "estimated_improvement": "预计提升 60-80% 查询性能"
            }
            suggestion = IndexSuggestion(**suggestion_data)
            session.add(suggestion)
            session.commit()
            session.refresh(suggestion)

            task = executor.create_index_suggestion_task(suggestion)

        return {
            "message": "索引优化任务创建成功",
            "task_id": task.id,
            "suggestion_id": suggestion.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建索引任务失败: {str(e)}")


@router.post("/tasks/{database_id}/rewrite-query")
async def create_query_rewrite_task(
    database_id: int,
    original_query: str = Query(..., min_length=1),
    rewritten_query: str = Query(..., min_length=1),
    executor: TuningExecutor = Depends(get_tuning_executor)
):
    """创建查询重写任务"""
    try:
        task = executor.create_query_rewrite_task(database_id, original_query, rewritten_query)
        return {
            "message": "查询重写任务创建成功",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建查询重写任务失败: {str(e)}")


@router.get("/tasks/statistics")
async def get_task_statistics(
    database_id: Optional[int] = None,
    executor: TuningExecutor = Depends(get_tuning_executor)
):
    """获取任务统计信息"""
    try:
        stats = executor.get_task_statistics(database_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务统计失败: {str(e)}")


@router.get("/index-suggestions/{database_id}", response_model=List[IndexSuggestionResponse])
async def get_index_suggestions(
    database_id: int,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """获取索引建议列表"""
    try:
        session = get_db_session(db)
        query = session.query(IndexSuggestion)\
            .filter(IndexSuggestion.database_id == database_id)

        if status:
            query = query.filter(IndexSuggestion.status == status)

        suggestions = query.order_by(IndexSuggestion.impact_score.desc())\
            .limit(limit)\
            .all()

        return [IndexSuggestionResponse.from_orm(suggestion) for suggestion in suggestions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取索引建议失败: {str(e)}")


@router.post("/background/collect-metrics/{database_id}")
async def start_background_metric_collection(
    database_id: int,
    background_tasks: BackgroundTasks,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """启动后台性能指标收集"""
    try:
        background_tasks.add_task(monitor.collect_system_metrics, database_id)
        return {"message": "后台指标收集已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动后台收集失败: {str(e)}")


@router.post("/background/capture-slow-queries/{database_id}")
async def start_background_slow_query_capture(
    database_id: int,
    background_tasks: BackgroundTasks,
    threshold_seconds: float = Query(1.0, ge=0.1),
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer)
):
    """启动后台慢查询捕获"""
    try:
        background_tasks.add_task(analyzer.capture_slow_queries, database_id, threshold_seconds)
        return {"message": "后台慢查询捕获已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动后台捕获失败: {str(e)}")


@router.post("/realtime-monitoring/{database_id}/start")
async def start_realtime_monitoring(
    database_id: int,
    interval_seconds: int = Query(60, ge=10, le=3600),
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """启动实时监控"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        result = provider.monitor.start_realtime(database_id, interval_seconds)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动实时监控失败: {str(e)}")


@router.post("/realtime-monitoring/{database_id}/stop")
async def stop_realtime_monitoring(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """停止实时监控"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        result = provider.monitor.stop_realtime(database_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止实时监控失败: {str(e)}")


@router.get("/monitoring-status/{database_id}")
async def get_monitoring_status(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """获取监控状态"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        status = provider.monitor.status(database_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控状态失败: {str(e)}")


@router.get("/alerts/{database_id}")
async def get_alerts(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """获取告警列表"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        alerts = provider.monitor.alerts(database_id)
        return {"alerts": alerts, "total": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警失败: {str(e)}")


@router.get("/recommendations/{database_id}")
async def get_system_recommendations(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """获取系统优化建议"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        recommendations = provider.monitor.recommendations(database_id)
        return {"recommendations": recommendations, "total": len(recommendations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取优化建议失败: {str(e)}")


@router.post("/reports/{database_id}/generate")
async def generate_performance_report(
    database_id: int,
    days: int = Query(7, ge=1, le=90),
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """生成性能报告"""
    try:
        provider = get_provider(get_sync_db_session(), database_id)
        report = provider.monitor.report(database_id, days)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成性能报告失败: {str(e)}")


@router.get("/realtime-metrics/{database_id}")
async def get_realtime_metrics(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """获取实时指标数据"""
    try:
        metrics = monitor.get_latest_metrics(database_id)
        alerts = monitor.check_alerts(database_id)
        recommendations = monitor.get_system_recommendations(database_id)

        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "alerts": alerts,
            "recommendations": recommendations,
            "system_health_score": 85.5  # 可以基于指标计算
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时指标失败: {str(e)}")


@router.post("/bulk-optimize/{database_id}")
async def bulk_optimize(
    database_id: int,
    background_tasks: BackgroundTasks,
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer),
    monitor: SystemMonitor = Depends(get_system_monitor)
):
    """批量优化操作"""
    try:
        # 启动多个后台任务
        background_tasks.add_task(analyzer.capture_slow_queries, database_id, 1.0)
        background_tasks.add_task(monitor.collect_system_metrics, database_id)
        background_tasks.add_task(monitor.perform_system_diagnosis, database_id)

        return {
            "message": "批量优化任务已启动",
            "tasks_started": [
                "慢查询捕获",
                "性能指标收集",
                "系统诊断"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量优化失败: {str(e)}")


@router.post("/analyze-execution-plan/{database_id}")
async def analyze_execution_plan(
    database_id: int,
    query_text: str = Query(..., min_length=1),
    analyzer: ExecutionPlanAnalyzer = Depends(get_execution_plan_analyzer)
):
    """分析SQL执行计划"""
    try:
        result = analyzer.analyze_execution_plan(database_id, query_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行计划分析失败: {str(e)}")


@router.get("/execution-plans/{database_id}")
async def get_execution_plans(
    database_id: int,
    limit: int = Query(50, ge=1, le=200),
    analyzer: ExecutionPlanAnalyzer = Depends(get_execution_plan_analyzer)
):
    """获取执行计划历史"""
    try:
        plans = analyzer.get_execution_plans_history(database_id, limit)
        return {
            "execution_plans": [
                {
                    "id": plan.id,
                    "query_text": plan.query_text[:100] + "..." if len(plan.query_text) > 100 else plan.query_text,
                    "query_hash": plan.query_hash,
                    "timestamp": plan.timestamp.isoformat(),
                    "plan_text": plan.plan_text,
                    "analysis_result": json.loads(plan.analysis_result) if plan.analysis_result else None
                } for plan in plans
            ],
            "total": len(plans)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行计划历史失败: {str(e)}")


@router.post("/compare-execution-plans")
async def compare_execution_plans(
    plan1_id: int = Query(..., description="第一个执行计划ID"),
    plan2_id: int = Query(..., description="第二个执行计划ID"),
    analyzer: ExecutionPlanAnalyzer = Depends(get_execution_plan_analyzer)
):
    """比较两个执行计划"""
    try:
        comparison = analyzer.compare_execution_plans(plan1_id, plan2_id)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行计划比较失败: {str(e)}")


@router.get("/execution-plan-visualization/{plan_id}")
async def get_execution_plan_visualization(
    plan_id: int,
    analyzer: ExecutionPlanAnalyzer = Depends(get_execution_plan_analyzer),
    db: AsyncSession = Depends(get_db)
):
    """获取执行计划可视化数据"""
    try:
        session = get_db_session(db)
        plan = session.query(ExecutionPlan).filter(ExecutionPlan.id == plan_id).first()

        if not plan:
            raise HTTPException(status_code=404, detail="执行计划不存在")

        visualization = analyzer.generate_plan_visualization(plan)
        return visualization
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成可视化数据失败: {str(e)}")


@router.post("/deep-query-analysis/{database_id}")
async def deep_query_analysis(
    database_id: int,
    query_text: str = Query(..., min_length=1),
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer),
    plan_analyzer: ExecutionPlanAnalyzer = Depends(get_execution_plan_analyzer)
):
    """深度查询分析（结合慢查询分析和执行计划分析）"""
    try:
        # 慢查询分析
        slow_analysis = analyzer.generate_optimization_suggestions(query_text, 1.0, 1000)

        # 执行计划分析
        plan_analysis = plan_analyzer.analyze_execution_plan(database_id, query_text)

        # 综合分析结果
        comprehensive_analysis = {
            "query_text": query_text,
            "slow_query_analysis": slow_analysis,
            "execution_plan_analysis": plan_analysis,
            "overall_assessment": {
                "performance_score": min(slow_analysis.get("priority_score", 0),
                                       json.loads(plan_analysis["analysis"]["performance_score"])),
                "risk_level": _calculate_risk_level(slow_analysis, plan_analysis),
                "optimization_priority": _calculate_optimization_priority(slow_analysis, plan_analysis)
            },
            "consolidated_recommendations": _consolidate_recommendations(
                slow_analysis.get("suggestions", []),
                plan_analysis.get("recommendations", [])
            )
        }

        return comprehensive_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"深度查询分析失败: {str(e)}")


def _calculate_risk_level(slow_analysis: Dict, plan_analysis: Dict) -> str:
    """计算查询风险等级"""
    slow_score = slow_analysis.get("priority_score", 0)
    plan_score = json.loads(plan_analysis["analysis"]).get("performance_score", 100)

    avg_score = (slow_score + (100 - plan_score)) / 2

    if avg_score > 75:
        return "critical"
    elif avg_score > 50:
        return "high"
    elif avg_score > 25:
        return "medium"
    else:
        return "low"


def _calculate_optimization_priority(slow_analysis: Dict, plan_analysis: Dict) -> str:
    """计算优化优先级"""
    slow_priority = slow_analysis.get("priority_score", 0)
    plan_bottlenecks = len(json.loads(plan_analysis["analysis"]).get("bottlenecks", []))

    if slow_priority > 70 or plan_bottlenecks > 3:
        return "urgent"
    elif slow_priority > 40 or plan_bottlenecks > 1:
        return "high"
    elif slow_priority > 20 or plan_bottlenecks > 0:
        return "medium"
    else:
        return "low"


def _consolidate_recommendations(slow_suggestions: List, plan_recommendations: List) -> List[Dict]:
    """整合优化建议"""
    all_recommendations = []

    # 添加慢查询建议
    for suggestion in slow_suggestions:
        all_recommendations.append({
            **suggestion,
            "source": "slow_query_analysis"
        })

    # 添加执行计划建议
    for recommendation in plan_recommendations:
        all_recommendations.append({
            **recommendation,
            "source": "execution_plan_analysis"
        })

    # 去重和排序
    unique_recommendations = []
    seen_titles = set()

    for rec in all_recommendations:
        title = rec.get("title", "")
        if title not in seen_titles:
            unique_recommendations.append(rec)
            seen_titles.add(title)

    # 按优先级排序
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    unique_recommendations.sort(key=lambda x: priority_order.get(x.get("impact", "low"), 3))

    return unique_recommendations[:10]  # 返回Top 10建议


# PostgreSQL特有的API接口

@router.get("/postgres/config-analysis/{database_id}")
async def analyze_postgres_config(
    database_id: int,
    optimizer: PostgreSQLConfigOptimizer = Depends(get_postgres_config_optimizer)
):
    """分析PostgreSQL配置"""
    try:
        analysis = optimizer.analyze_configuration(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL配置分析失败: {str(e)}")


@router.get("/postgres/vacuum-strategy/{database_id}")
async def get_vacuum_strategy(
    database_id: int,
    optimizer: PostgreSQLConfigOptimizer = Depends(get_postgres_config_optimizer)
):
    """获取VACUUM维护策略"""
    try:
        strategy = optimizer.generate_vacuum_strategy(database_id)
        return strategy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VACUUM策略生成失败: {str(e)}")


@router.post("/postgres/optimize-memory/{database_id}")
async def optimize_memory_settings(
    database_id: int,
    system_info: Dict[str, Any],
    optimizer: PostgreSQLConfigOptimizer = Depends(get_postgres_config_optimizer)
):
    """优化PostgreSQL内存设置"""
    try:
        optimization = optimizer.optimize_memory_settings(system_info)
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内存优化失败: {str(e)}")


@router.post("/postgres/optimize-connections/{database_id}")
async def optimize_connection_settings(
    database_id: int,
    workload_info: Dict[str, Any],
    optimizer: PostgreSQLConfigOptimizer = Depends(get_postgres_config_optimizer)
):
    """优化PostgreSQL连接设置"""
    try:
        optimization = optimizer.optimize_connection_settings(workload_info)
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接优化失败: {str(e)}")


@router.post("/postgres/generate-tuning-script/{database_id}")
async def generate_tuning_script(
    database_id: int,
    analysis_results: Dict[str, Any],
    optimizer: PostgreSQLConfigOptimizer = Depends(get_postgres_config_optimizer)
):
    """生成PostgreSQL性能调优脚本"""
    try:
        script = optimizer.generate_performance_tuning_script(analysis_results)
        return {
            "tuning_script": script,
            "generated_at": datetime.now().isoformat(),
            "description": "PostgreSQL性能调优配置脚本，包含内存、连接和维护优化"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调优脚本生成失败: {str(e)}")


@router.post("/postgres/create-vacuum-task/{database_id}")
async def create_vacuum_task(
    database_id: int,
    table_name: str = Query(..., description="表名"),
    vacuum_type: str = Query("VACUUM", description="VACUUM类型: VACUUM, VACUUM FULL, VACUUM ANALYZE"),
    executor: TuningExecutor = Depends(get_tuning_executor)
):
    """创建VACUUM维护任务"""
    try:
        task = executor.create_vacuum_task(database_id, table_name, vacuum_type)
        return {
            "message": "VACUUM任务创建成功",
            "task_id": task.id,
            "task_name": task.task_name,
            "vacuum_type": vacuum_type,
            "table_name": table_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VACUUM任务创建失败: {str(e)}")


@router.post("/postgres/create-analyze-task/{database_id}")
async def create_analyze_task(
    database_id: int,
    table_name: str = Query(..., description="表名"),
    executor: TuningExecutor = Depends(get_tuning_executor)
):
    """创建ANALYZE统计信息更新任务"""
    try:
        task = executor.create_analyze_task(database_id, table_name)
        return {
            "message": "ANALYZE任务创建成功",
            "task_id": task.id,
            "task_name": task.task_name,
            "table_name": table_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ANALYZE任务创建失败: {str(e)}")


@router.post("/postgres/create-reindex-task/{database_id}")
async def create_reindex_task(
    database_id: int,
    index_name: str = Query(..., description="索引名"),
    executor: TuningExecutor = Depends(get_tuning_executor)
):
    """创建REINDEX索引重建任务"""
    try:
        task = executor.create_reindex_task(database_id, index_name)
        return {
            "message": "REINDEX任务创建成功",
            "task_id": task.id,
            "task_name": task.task_name,
            "index_name": index_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"REINDEX任务创建失败: {str(e)}")


@router.get("/postgres/table-health/{database_id}")
async def get_table_health_analysis(
    database_id: int,
    optimizer: PostgreSQLConfigOptimizer = Depends(get_postgres_config_optimizer)
):
    """获取表健康状况分析"""
    try:
        table_health = optimizer._analyze_table_health(database_id)
        return {
            "table_health_analysis": table_health,
            "analyzed_at": datetime.now().isoformat(),
            "recommendations": _generate_table_health_recommendations(table_health)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"表健康分析失败: {str(e)}")


@router.get("/postgres/index-recommendations/{database_id}")
async def get_postgres_index_recommendations(
    database_id: int,
    analyzer: SlowQueryAnalyzer = Depends(get_slow_query_analyzer)
):
    """获取PostgreSQL索引优化建议"""
    try:
        # 获取慢查询分析结果
        slow_queries = analyzer.get_slow_queries(database_id, limit=50)

        # 生成PostgreSQL特有的索引建议
        recommendations = []
        for query in slow_queries:
            if query.execution_time > 1.0:  # 只分析慢查询
                analysis = analyzer.generate_optimization_suggestions(
                    query.query_text, query.execution_time, query.rows_examined
                )

                # 提取PostgreSQL特有的索引建议
                for suggestion in analysis.get("suggestions", []):
                    if "index" in suggestion.get("type", "").lower():
                        recommendations.append({
                            "query_id": query.id,
                            "query_text": query.query_text[:100] + "...",
                            "suggestion": suggestion,
                            "execution_time": query.execution_time,
                            "rows_examined": query.rows_examined
                        })

        return {
            "index_recommendations": recommendations[:20],  # Top 20建议
            "total_analyzed_queries": len(slow_queries),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引建议生成失败: {str(e)}")


@router.get("/postgres/performance-insights/{database_id}")
async def get_postgres_performance_insights(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor),
    optimizer: PostgreSQLConfigOptimizer = Depends(get_postgres_config_optimizer)
):
    """获取PostgreSQL性能洞察"""
    try:
        # 获取最新指标
        latest_metrics = monitor.get_latest_metrics(database_id)

        # 获取配置分析
        config_analysis = optimizer.analyze_configuration(database_id)

        # 获取VACUUM策略
        vacuum_strategy = optimizer.generate_vacuum_strategy(database_id)

        # 生成综合洞察
        insights = {
            "performance_score": _calculate_postgres_performance_score(latest_metrics),
            "bottlenecks": _identify_postgres_bottlenecks(latest_metrics),
            "optimization_opportunities": _generate_postgres_optimization_opportunities(
                latest_metrics, config_analysis, vacuum_strategy
            ),
            "health_status": _assess_postgres_health(latest_metrics),
            "generated_at": datetime.now().isoformat()
        }

        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能洞察生成失败: {str(e)}")


def _generate_table_health_recommendations(table_health: Dict[str, Any]) -> List[Dict[str, Any]]:
    """生成表健康建议"""
    recommendations = []

    # 严重膨胀的表
    for table in table_health["critical_tables"]:
        recommendations.append({
            "table": table["name"],
            "priority": "critical",
            "action": "VACUUM FULL",
            "reason": f"表膨胀比率 {table['bloat_ratio']:.2f}，影响性能",
            "estimated_improvement": "显著提升查询性能"
        })

    # 需要定期维护的表
    for table in table_health["warning_tables"]:
        recommendations.append({
            "table": table["name"],
            "priority": "medium",
            "action": "VACUUM ANALYZE",
            "reason": f"表需要定期维护，当前膨胀比率 {table['bloat_ratio']:.2f}",
            "estimated_improvement": "提升查询性能"
        })

    return recommendations


def _calculate_postgres_performance_score(metrics: Dict[str, Any]) -> float:
    """计算PostgreSQL性能评分"""
    score = 100.0

    if "postgresql" in metrics:
        pg_metrics = metrics["postgresql"]

        # 缓冲区命中率评分
        buffer_hit_ratio = pg_metrics["buffer_hit_ratio"]
        if buffer_hit_ratio < 90:
            score -= (90 - buffer_hit_ratio) * 0.5

        # 锁等待评分
        waiting_locks = pg_metrics["locks"]["waiting_locks"]
        if waiting_locks > 5:
            score -= waiting_locks * 2

        # 临时文件评分
        temp_files = pg_metrics["temp_files"]["files_created_per_hour"]
        if temp_files > 10:
            score -= temp_files * 1.5

        # 表膨胀评分
        bloat_ratio = pg_metrics["table_health"]["avg_bloat_ratio"]
        if bloat_ratio > 1.5:
            score -= (bloat_ratio - 1.5) * 20

    return max(0.0, score)


def _identify_postgres_bottlenecks(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """识别PostgreSQL性能瓶颈"""
    bottlenecks = []

    if "postgresql" in metrics:
        pg_metrics = metrics["postgresql"]

        # 缓冲区命中率瓶颈
        if pg_metrics["buffer_hit_ratio"] < 90:
            bottlenecks.append({
                "type": "buffer_hit_ratio",
                "severity": "high" if pg_metrics["buffer_hit_ratio"] < 80 else "medium",
                "description": f"缓冲区命中率偏低: {pg_metrics['buffer_hit_ratio']:.1f}%",
                "impact": "查询性能下降"
            })

        # 锁等待瓶颈
        if pg_metrics["locks"]["waiting_locks"] > 3:
            bottlenecks.append({
                "type": "lock_waiting",
                "severity": "high" if pg_metrics["locks"]["waiting_locks"] > 5 else "medium",
                "description": f"锁等待过多: {pg_metrics['locks']['waiting_locks']} 个等待锁",
                "impact": "并发性能下降"
            })

        # 临时文件瓶颈
        if pg_metrics["temp_files"]["files_created_per_hour"] > 10:
            bottlenecks.append({
                "type": "temp_file_usage",
                "severity": "medium",
                "description": f"临时文件创建频繁: {pg_metrics['temp_files']['files_created_per_hour']} 个/小时",
                "impact": "磁盘I/O增加"
            })

        # 表膨胀瓶颈
        if pg_metrics["table_health"]["avg_bloat_ratio"] > 2.0:
            bottlenecks.append({
                "type": "table_bloat",
                "severity": "high",
                "description": f"表膨胀严重: 平均膨胀比率为 {pg_metrics['table_health']['avg_bloat_ratio']:.2f}",
                "impact": "存储空间浪费，查询性能下降"
            })

    return bottlenecks


def _generate_postgres_optimization_opportunities(
    metrics: Dict[str, Any],
    config_analysis: Dict[str, Any],
    vacuum_strategy: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """生成PostgreSQL优化机会"""
    opportunities = []

    # 配置优化机会
    if config_analysis.get("optimization_score", 100) < 80:
        opportunities.append({
            "type": "configuration",
            "title": "配置优化",
            "description": "PostgreSQL配置可以进一步优化",
            "estimated_benefit": "10-30% 性能提升",
            "effort": "medium"
        })

    # VACUUM优化机会
    if vacuum_strategy.get("immediate_actions"):
        opportunities.append({
            "type": "vacuum",
            "title": "VACUUM维护优化",
            "description": f"发现 {len(vacuum_strategy['immediate_actions'])} 个表需要紧急VACUUM",
            "estimated_benefit": "15-40% 性能提升",
            "effort": "medium"
        })

    # 内存优化机会
    if metrics.get("memory", {}).get("usage_percent", 0) > 85:
        opportunities.append({
            "type": "memory",
            "title": "内存配置优化",
            "description": "内存使用率较高，可能影响性能",
            "estimated_benefit": "20-35% 性能提升",
            "effort": "high"
        })

    return opportunities


def _assess_postgres_health(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """评估PostgreSQL整体健康状况"""
    performance_score = _calculate_postgres_performance_score(metrics)
    bottlenecks = _identify_postgres_bottlenecks(metrics)

    if performance_score >= 90 and len(bottlenecks) == 0:
        health_status = "excellent"
        description = "PostgreSQL运行状况优秀"
    elif performance_score >= 75 and len(bottlenecks) <= 1:
        health_status = "good"
        description = "PostgreSQL运行状况良好"
    elif performance_score >= 60:
        health_status = "fair"
        description = "PostgreSQL运行状况一般，需要关注"
    elif performance_score >= 40:
        health_status = "poor"
        description = "PostgreSQL运行状况较差，需要优化"
    else:
        health_status = "critical"
        description = "PostgreSQL运行状况严重，需要立即处理"

    return {
        "status": health_status,
        "description": description,
        "performance_score": performance_score,
        "bottlenecks_count": len(bottlenecks),
        "critical_issues": len([b for b in bottlenecks if b["severity"] == "critical"])
    }
