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
from app.services.performance_tuning.mysql_enhanced_optimizer import MySQLEnhancedOptimizer
from app.services.performance_tuning.oceanbase_config_optimizer import OceanBaseConfigOptimizer
from app.services.db_providers.registry import get_provider, get_database_type_name

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


def get_mysql_enhanced_optimizer(session: Session = Depends(get_sync_db_session)) -> MySQLEnhancedOptimizer:
    """获取MySQL增强优化器实例"""
    return MySQLEnhancedOptimizer(session)
def get_oceanbase_optimizer(session: Session = Depends(get_sync_db_session)) -> OceanBaseConfigOptimizer:
    """获取OceanBase配置优化器实例"""
    return OceanBaseConfigOptimizer(session)



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
        # 为每个查询添加数据源标识
        result = []
        for query in slow_queries:
            query_dict = SlowQueryResponse.from_orm(query).dict()
            query_dict['source'] = 'mock_data'  # MySQL数据标记为演示数据
            result.append(query_dict)
        return result
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

        # 为每个指标添加数据源标识
        result = []
        for metric in metrics:
            metric_dict = PerformanceMetricResponse.from_orm(metric).dict()
            metric_dict['source'] = 'mock_data'  # MySQL数据标记为演示数据
            result.append(metric_dict)
        return result
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

        # 为每个诊断添加数据源标识
        result = []
        for diagnosis in diagnoses:
            diagnosis_dict = SystemDiagnosisResponse.from_orm(diagnosis).dict()
            diagnosis_dict['source'] = 'mock_data'  # MySQL数据标记为演示数据
            result.append(diagnosis_dict)
        return result
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
        if database_id:
            # 检查数据库类型
            db_type = get_database_type_name(get_sync_db_session(), database_id)
            
            if db_type == "mysql":
                # 对于MySQL，直接从MySQL数据库查询
                from sqlalchemy import create_engine, text
                
                mysql_engine = create_engine(
                    f"mysql+pymysql://udbm_mysql_user:udbm_mysql_password@localhost:3306/udbm_mysql_demo?charset=utf8mb4&use_unicode=1",
                    echo=False,
                    connect_args={"charset": "utf8mb4"}
                )
                
                with mysql_engine.connect() as conn:
                    query_sql = """
                        SELECT id, database_id, task_type, task_name, description, task_config,
                               execution_sql, status, priority, execution_result, error_message,
                               scheduled_at, started_at, completed_at, related_suggestion_id,
                               created_by, created_at, updated_at
                        FROM tuning_tasks 
                        WHERE database_id = :db_id
                    """
                    params = {"db_id": database_id}
                    
                    if status:
                        query_sql += " AND status = :status"
                        params["status"] = status
                    
                    query_sql += " ORDER BY created_at DESC LIMIT :limit"
                    params["limit"] = limit
                    
                    result = conn.execute(text(query_sql), params)
                    rows = result.fetchall()
                    
                    # 转换为响应格式
                    tasks = []
                    for row in rows:
                        # 根据任务类型和表名生成正确的中文描述
                        task_name_map = {
                            "index_creation": {
                                "users": "为表 users 创建索引",
                                "products": "为表 products 创建索引", 
                                "orders": "为表 orders 创建复合索引",
                                "inventory": "为表 inventory 创建索引",
                                "logs": "为表 logs 创建索引"
                            },
                            "analyze": {
                                "users": "分析表 users 统计信息",
                                "products": "分析表 products 统计信息",
                                "orders": "分析表 orders 统计信息",
                                "inventory": "分析表 inventory 统计信息",
                                "logs": "分析表 logs 统计信息"
                            },
                            "query_rewrite": "查询重写优化"
                        }
                        
                        description_map = {
                            "index_creation": {
                                "users": "创建 users.created_at 索引以优化用户查询性能，预计提升70-80%查询性能",
                                "products": "创建 products.status 索引以优化商品状态查询，预计提升60-75%查询性能",
                                "orders": "创建 orders 表复合索引以优化用户订单查询，预计提升65-85%查询性能",
                                "inventory": "创建 inventory.product_id 索引以优化库存更新操作，预计提升80-90%更新性能",
                                "logs": "创建 logs.created_at 索引以优化日志清理任务，预计提升85-95%清理性能"
                            },
                            "analyze": {
                                "users": "更新表 users 的统计信息以优化查询计划，提升查询优化器决策准确性",
                                "products": "更新表 products 的统计信息以优化查询计划",
                                "orders": "更新表 orders 的统计信息以优化查询计划",
                                "inventory": "更新表 inventory 的统计信息以优化查询计划",
                                "logs": "更新表 logs 的统计信息以优化查询计划"
                            },
                            "query_rewrite": "重写低效查询以提升性能，优化JOIN操作和WHERE条件"
                        }
                        
                        task_type = row[2]
                        task_config = row[5] if isinstance(row[5], dict) else eval(row[5]) if isinstance(row[5], str) else {}
                        table_name = task_config.get('table_name', '') if isinstance(task_config, dict) else ''
                        
                        if task_type in task_name_map and isinstance(task_name_map[task_type], dict):
                            task_name = task_name_map[task_type].get(table_name, f"为表 {table_name} 创建索引")
                        elif task_type in task_name_map:
                            task_name = task_name_map[task_type]
                        else:
                            task_name = row[3]
                            
                        if task_type in description_map and isinstance(description_map[task_type], dict):
                            description = description_map[task_type].get(table_name, f"优化表 {table_name} 的性能")
                        elif task_type in description_map:
                            description = description_map[task_type]
                        else:
                            description = row[4]
                        
                        task = {
                            "id": row[0],
                            "database_id": row[1],
                            "task_type": row[2],
                            "task_name": task_name,
                            "description": description,
                            "task_config": task_config,
                            "execution_sql": row[6],
                            "status": row[7],
                            "priority": row[8],
                            "execution_result": row[9],
                            "error_message": row[10],
                            "scheduled_at": row[11],
                            "started_at": row[12],
                            "completed_at": row[13],
                            "related_suggestion_id": row[14],
                            "created_by": row[15],
                            "created_at": row[16],
                            "updated_at": row[17],
                            "source": "mock_data"
                        }
                        tasks.append(task)
                    
                    return tasks
            else:
                # 对于PostgreSQL，使用原有逻辑
                session = get_db_session(db)
                query = session.query(TuningTask).filter(TuningTask.database_id == database_id)

                if status:
                    query = query.filter(TuningTask.status == status)

                tasks = query.order_by(TuningTask.created_at.desc()).limit(limit).all()

                # 为每个任务添加数据源标识
                result = []
                for task in tasks:
                    task_dict = TuningTaskResponse.from_orm(task).dict()
                    task_dict['source'] = 'postgresql_data'
                    result.append(task_dict)
                return result
        else:
            # 没有指定database_id时，查询所有任务
            session = get_db_session(db)
            query = session.query(TuningTask)

            if status:
                query = query.filter(TuningTask.status == status)

            tasks = query.order_by(TuningTask.created_at.desc()).limit(limit).all()

            # 为每个任务添加数据源标识
            result = []
            for task in tasks:
                task_dict = TuningTaskResponse.from_orm(task).dict()
                task_dict['source'] = 'postgresql_data'
                result.append(task_dict)
            return result
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
        # 使用Provider抽象以支持多数据库
        provider = get_provider(get_sync_db_session(), database_id)
        
        # 检查数据库类型
        db_type = get_database_type_name(get_sync_db_session(), database_id)
        
        if db_type == "mysql":
            # 对于MySQL，使用pymysql直接连接
            import pymysql
            import json
            
            connection = pymysql.connect(
                host='localhost',
                user='udbm_mysql_user',
                password='udbm_mysql_password',
                database='udbm_mysql_demo',
                charset='utf8mb4',
                use_unicode=True,
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with connection.cursor() as cursor:
                    # 强制设置字符集
                    cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
                    cursor.execute("SET CHARACTER SET utf8mb4")
                    
                    query_sql = """
                        SELECT id, database_id, table_name, column_names, index_type, suggestion_type,
                               reason, impact_score, estimated_improvement, status, applied_at, applied_by,
                               related_query_ids, created_at, updated_at
                        FROM index_suggestions 
                        WHERE database_id = %s
                    """
                    params = [database_id]
                    
                    if status:
                        query_sql += " AND status = %s"
                        params.append(status)
                    
                    query_sql += " ORDER BY impact_score DESC LIMIT %s"
                    params.append(limit)
                    
                    cursor.execute(query_sql, params)
                    rows = cursor.fetchall()
                    
                    # 转换为响应格式
                    suggestions = []
                    for row in rows:
                        # 处理JSON字段
                        column_names = row['column_names']
                        if isinstance(column_names, str):
                            try:
                                column_names = json.loads(column_names)
                            except:
                                column_names = []
                        
                        related_query_ids = row['related_query_ids']
                        if isinstance(related_query_ids, str):
                            try:
                                related_query_ids = json.loads(related_query_ids)
                            except:
                                related_query_ids = []
                        
                        # 根据表名和列名生成正确的中文描述
                        reason_map = {
                            "inventory": "库存更新操作频繁，产品ID查询缺少索引，导致锁等待时间过长。",
                            "users": "检测到频繁按创建时间查询用户，但缺少相应索引。查询平均执行时间2.45秒，影响用户体验。",
                            "orders": "用户订单查询和时间范围查询频繁，需要复合索引优化。当前查询涉及大量行扫描。",
                            "products": "产品状态查询频繁，缺少索引导致全表扫描。影响商品列表和统计查询性能。",
                            "logs": "日志清理任务需要按时间范围删除，缺少时间索引导致全表扫描。"
                        }
                        
                        improvement_map = {
                            "inventory": "预计更新性能提升80-90%，减少锁等待时间",
                            "users": "预计查询性能提升70-80%，响应时间减少至0.3秒以内",
                            "orders": "预计查询性能提升65-85%，用户订单页面加载速度显著提升",
                            "products": "预计查询性能提升60-75%，特别是商品筛选功能",
                            "logs": "预计清理任务性能提升85-95%，减少系统维护时间"
                        }
                        
                        table_name = row['table_name']
                        reason = reason_map.get(table_name, "系统检测到性能优化机会，建议创建相应索引。")
                        improvement = improvement_map.get(table_name, "预计查询性能显著提升")
                        
                        suggestion = {
                            "id": row['id'],
                            "database_id": row['database_id'],
                            "table_name": row['table_name'],
                            "column_names": column_names,
                            "index_type": row['index_type'],
                            "suggestion_type": row['suggestion_type'],
                            "reason": f"{reason} (AI生成)",
                            "impact_score": row['impact_score'],
                            "estimated_improvement": f"{improvement} (AI生成)",
                            "status": row['status'],
                            "applied_at": row['applied_at'],
                            "applied_by": row['applied_by'],
                            "related_query_ids": related_query_ids,
                            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                            "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                            "source": "mock_data"
                        }
                        suggestions.append(suggestion)
                    
                    return suggestions
            finally:
                connection.close()
        else:
            # 对于PostgreSQL，使用原有逻辑
            session = get_db_session(db)
            query = session.query(IndexSuggestion)\
                .filter(IndexSuggestion.database_id == database_id)

            if status:
                query = query.filter(IndexSuggestion.status == status)

            suggestions = query.order_by(IndexSuggestion.impact_score.desc())\
                .limit(limit)\
                .all()

            # 为每个建议添加数据源标识
            result = []
            for suggestion in suggestions:
                suggestion_dict = IndexSuggestionResponse.from_orm(suggestion).dict()
                suggestion_dict['source'] = 'postgresql_data'
                result.append(suggestion_dict)
            return result
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
    db: AsyncSession = Depends(get_db)
):
    """获取执行计划历史"""
    try:
        session = get_db_session(db)
        plans = session.query(ExecutionPlan)\
            .filter(ExecutionPlan.database_id == database_id)\
            .order_by(ExecutionPlan.timestamp.desc())\
            .limit(limit)\
            .all()
        
        return {
            "execution_plans": [
                {
                    "id": plan.id,
                    "query_text": plan.query_text[:100] + "..." if len(plan.query_text) > 100 else plan.query_text,
                    "query_hash": plan.query_hash,
                    "timestamp": plan.timestamp.isoformat(),
                    "plan_text": plan.plan_text,
                    "analysis_result": json.loads(plan.analysis_result) if plan.analysis_result else None,
                    "source": "mock_data"  # MySQL数据标记为演示数据
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


# =====================================
# MySQL 增强调优 API 接口
# =====================================

@router.get("/mysql/config-analysis/{database_id}")
async def analyze_mysql_config(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """分析MySQL配置"""
    try:
        analysis = optimizer.analyze_configuration(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL配置分析失败: {str(e)}")


@router.get("/mysql/storage-engine-analysis/{database_id}")
async def analyze_mysql_storage_engine(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """分析MySQL存储引擎优化"""
    try:
        analysis = optimizer.analyze_storage_engine_optimization(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL存储引擎分析失败: {str(e)}")


@router.get("/mysql/hardware-analysis/{database_id}")
async def analyze_mysql_hardware(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """分析MySQL硬件优化建议"""
    try:
        analysis = optimizer.analyze_hardware_optimization(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL硬件分析失败: {str(e)}")


@router.get("/mysql/security-analysis/{database_id}")
async def analyze_mysql_security(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """分析MySQL安全配置优化"""
    try:
        analysis = optimizer.analyze_security_optimization(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL安全分析失败: {str(e)}")


@router.get("/mysql/replication-analysis/{database_id}")
async def analyze_mysql_replication(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """分析MySQL主从复制优化"""
    try:
        analysis = optimizer.analyze_replication_optimization(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL复制分析失败: {str(e)}")


@router.get("/mysql/partition-analysis/{database_id}")
async def analyze_mysql_partition(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """分析MySQL分区表优化"""
    try:
        analysis = optimizer.analyze_partition_optimization(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL分区分析失败: {str(e)}")


@router.get("/mysql/backup-analysis/{database_id}")
async def analyze_mysql_backup(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """分析MySQL备份恢复策略"""
    try:
        analysis = optimizer.analyze_backup_recovery_optimization(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL备份分析失败: {str(e)}")


@router.post("/mysql/generate-tuning-script/{database_id}")
async def generate_mysql_tuning_script(
    database_id: int,
    optimization_areas: List[str] = Query(default=None, description="优化区域: config, storage, security, replication"),
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """生成MySQL性能调优脚本"""
    try:
        script = optimizer.generate_comprehensive_tuning_script(database_id, optimization_areas)
        return {
            "tuning_script": script,
            "generated_at": datetime.now().isoformat(),
            "database_id": database_id,
            "optimization_areas": optimization_areas or ["config", "storage", "security", "replication"],
            "description": "MySQL综合性能调优脚本，包含多维度优化配置"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL调优脚本生成失败: {str(e)}")


@router.get("/mysql/optimization-summary/{database_id}")
async def get_mysql_optimization_summary(
    database_id: int,
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """获取MySQL优化总结"""
    try:
        summary = optimizer.get_optimization_summary(database_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL优化总结生成失败: {str(e)}")


@router.post("/mysql/comprehensive-analysis/{database_id}")
async def comprehensive_mysql_analysis(
    database_id: int,
    include_areas: List[str] = Query(
        default=["config", "storage", "hardware", "security", "replication", "partition", "backup"],
        description="包含的分析区域"
    ),
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """MySQL综合分析 - 一次性获取所有维度的分析结果"""
    try:
        comprehensive_analysis = {
            "database_id": database_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "included_areas": include_areas,
            "analysis_results": {}
        }
        
        if "config" in include_areas:
            comprehensive_analysis["analysis_results"]["config"] = optimizer.analyze_configuration(database_id)
            
        if "storage" in include_areas:
            comprehensive_analysis["analysis_results"]["storage"] = optimizer.analyze_storage_engine_optimization(database_id)
            
        if "hardware" in include_areas:
            comprehensive_analysis["analysis_results"]["hardware"] = optimizer.analyze_hardware_optimization(database_id)
            
        if "security" in include_areas:
            comprehensive_analysis["analysis_results"]["security"] = optimizer.analyze_security_optimization(database_id)
            
        if "replication" in include_areas:
            comprehensive_analysis["analysis_results"]["replication"] = optimizer.analyze_replication_optimization(database_id)
            
        if "partition" in include_areas:
            comprehensive_analysis["analysis_results"]["partition"] = optimizer.analyze_partition_optimization(database_id)
            
        if "backup" in include_areas:
            comprehensive_analysis["analysis_results"]["backup"] = optimizer.analyze_backup_recovery_optimization(database_id)
        
        # 生成综合总结
        comprehensive_analysis["summary"] = optimizer.get_optimization_summary(database_id)
        
        return comprehensive_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL综合分析失败: {str(e)}")


@router.get("/mysql/performance-insights/{database_id}")
async def get_mysql_performance_insights(
    database_id: int,
    monitor: SystemMonitor = Depends(get_system_monitor),
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """获取MySQL性能洞察"""
    try:
        # 获取最新指标
        latest_metrics = monitor.get_latest_metrics(database_id)
        
        # 获取配置分析
        config_analysis = optimizer.analyze_configuration(database_id)
        
        # 获取优化总结
        optimization_summary = optimizer.get_optimization_summary(database_id)
        
        # 生成综合洞察
        insights = {
            "database_id": database_id,
            "performance_score": optimization_summary.get("overall_health_score", 70.0),
            "bottlenecks": _identify_mysql_bottlenecks(latest_metrics, config_analysis),
            "optimization_opportunities": _generate_mysql_optimization_opportunities(
                latest_metrics, config_analysis, optimization_summary
            ),
            "health_status": _assess_mysql_health(optimization_summary),
            "key_metrics": {
                "cpu_usage": latest_metrics.get("cpu", {}).get("usage_percent", 0),
                "memory_usage": latest_metrics.get("memory", {}).get("usage_percent", 0),
                "active_connections": latest_metrics.get("connections", {}).get("active", 0),
                "qps": latest_metrics.get("throughput", {}).get("qps", 0)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL性能洞察生成失败: {str(e)}")


@router.post("/mysql/quick-optimization/{database_id}")
async def quick_mysql_optimization(
    database_id: int,
    focus_area: str = Query("performance", description="优化重点: performance, security, reliability"),
    optimizer: MySQLEnhancedOptimizer = Depends(get_mysql_enhanced_optimizer)
):
    """MySQL快速优化建议"""
    try:
        # 根据重点区域提供针对性建议
        quick_recommendations = []
        
        if focus_area == "performance":
            config_analysis = optimizer.analyze_configuration(database_id)
            storage_analysis = optimizer.analyze_storage_engine_optimization(database_id)
            
            # 提取高影响性能建议
            for rec in config_analysis.get("recommendations", []):
                if rec.get("impact") == "high":
                    quick_recommendations.append({
                        "category": "配置优化",
                        "action": rec.get("description"),
                        "impact": "high",
                        "estimated_improvement": rec.get("estimated_improvement"),
                        "sql": f"SET GLOBAL {rec.get('parameter')} = {rec.get('recommended_value')};"
                    })
            
        elif focus_area == "security":
            security_analysis = optimizer.analyze_security_optimization(database_id)
            
            # 提取高危安全建议
            for category in security_analysis.values():
                if isinstance(category, dict) and "recommendations" in category:
                    for rec in category["recommendations"]:
                        if rec.get("severity") == "high":
                            quick_recommendations.append({
                                "category": "安全加固",
                                "action": rec.get("solution"),
                                "impact": "critical",
                                "sql": rec.get("sql", "-- 需要手动配置")
                            })
                            
        elif focus_area == "reliability":
            replication_analysis = optimizer.analyze_replication_optimization(database_id)
            backup_analysis = optimizer.analyze_backup_recovery_optimization(database_id)
            
            # 提取可靠性建议
            for rec in backup_analysis.get("optimization_recommendations", []):
                if rec.get("severity") in ["high", "medium"]:
                    quick_recommendations.append({
                        "category": "可靠性提升",
                        "action": rec.get("solution"),
                        "impact": rec.get("severity"),
                        "benefits": rec.get("benefits", [])
                    })
        
        return {
            "database_id": database_id,
            "focus_area": focus_area,
            "quick_recommendations": quick_recommendations[:5],  # 前5个建议
            "generated_at": datetime.now().isoformat(),
            "next_steps": [
                "执行高优先级建议",
                "监控性能变化",
                "定期评估优化效果"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL快速优化失败: {str(e)}")


# =====================================
# OceanBase 调优 API 接口
# =====================================

@router.get("/oceanbase/config-analysis/{database_id}")
async def analyze_oceanbase_config(
    database_id: int,
    optimizer: OceanBaseConfigOptimizer = Depends(get_oceanbase_optimizer)
):
    """分析OceanBase配置"""
    try:
        analysis = optimizer.analyze_configuration(database_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OceanBase配置分析失败: {str(e)}")


@router.get("/oceanbase/maintenance-strategy/{database_id}")
async def get_oceanbase_maintenance_strategy(
    database_id: int,
    optimizer: OceanBaseConfigOptimizer = Depends(get_oceanbase_optimizer)
):
    """获取OceanBase维护策略（合并/统计等）"""
    try:
        strategy = optimizer.generate_maintenance_strategy(database_id)
        return strategy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"维护策略生成失败: {str(e)}")


@router.post("/oceanbase/generate-tuning-script/{database_id}")
async def generate_oceanbase_tuning_script(
    database_id: int,
    analysis_results: Dict[str, Any],
    optimizer: OceanBaseConfigOptimizer = Depends(get_oceanbase_optimizer)
):
    """生成OceanBase性能调优脚本"""
    try:
        script = optimizer.generate_performance_tuning_script(analysis_results)
        return {
            "tuning_script": script,
            "generated_at": datetime.now().isoformat(),
            "description": "OceanBase性能调优脚本，包含内存、计划缓存、合并策略等优化建议"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OceanBase调优脚本生成失败: {str(e)}")


def _identify_mysql_bottlenecks(metrics: Dict[str, Any], config_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """识别MySQL性能瓶颈"""
    bottlenecks = []
    
    # CPU瓶颈
    cpu_usage = metrics.get("cpu", {}).get("usage_percent", 0)
    if cpu_usage > 80:
        bottlenecks.append({
            "type": "cpu",
            "severity": "high" if cpu_usage > 90 else "medium",
            "description": f"CPU使用率过高 ({cpu_usage:.1f}%)",
            "impact": "查询响应时间增加"
        })
    
    # 内存瓶颈
    memory_usage = metrics.get("memory", {}).get("usage_percent", 0)
    if memory_usage > 85:
        bottlenecks.append({
            "type": "memory",
            "severity": "high" if memory_usage > 95 else "medium",
            "description": f"内存使用率过高 ({memory_usage:.1f}%)",
            "impact": "可能导致swap使用，严重影响性能"
        })
    
    # 连接瓶颈
    active_connections = metrics.get("connections", {}).get("active", 0)
    max_connections = metrics.get("connections", {}).get("max_connections", 100)
    if active_connections > max_connections * 0.8:
        bottlenecks.append({
            "type": "connections",
            "severity": "medium",
            "description": f"连接数接近上限 ({active_connections}/{max_connections})",
            "impact": "新连接可能被拒绝"
        })
    
    return bottlenecks


def _generate_mysql_optimization_opportunities(
    metrics: Dict[str, Any],
    config_analysis: Dict[str, Any],
    optimization_summary: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """生成MySQL优化机会"""
    opportunities = []
    
    # 配置优化机会
    optimization_score = config_analysis.get("optimization_score", 100)
    if optimization_score < 80:
        opportunities.append({
            "type": "configuration",
            "title": "配置参数优化",
            "description": "MySQL配置参数存在优化空间",
            "estimated_benefit": "20-40% 性能提升",
            "effort": "medium"
        })
    
    # 高影响建议数量
    high_impact_count = optimization_summary.get("optimization_statistics", {}).get("high_impact_recommendations", 0)
    if high_impact_count > 3:
        opportunities.append({
            "type": "high_impact_tuning",
            "title": "高影响调优",
            "description": f"发现 {high_impact_count} 个高影响优化建议",
            "estimated_benefit": "30-60% 性能提升",
            "effort": "medium"
        })
    
    # 安全问题
    critical_security = optimization_summary.get("optimization_statistics", {}).get("critical_security_issues", 0)
    if critical_security > 0:
        opportunities.append({
            "type": "security",
            "title": "安全配置加固",
            "description": f"发现 {critical_security} 个严重安全配置问题",
            "estimated_benefit": "显著提高系统安全性",
            "effort": "high"
        })
    
    return opportunities


def _assess_mysql_health(optimization_summary: Dict[str, Any]) -> Dict[str, Any]:
    """评估MySQL整体健康状况"""
    health_score = optimization_summary.get("overall_health_score", 70.0)
    critical_issues = optimization_summary.get("optimization_statistics", {}).get("critical_security_issues", 0)
    
    if health_score >= 90 and critical_issues == 0:
        health_status = "excellent"
        description = "MySQL运行状况优秀"
    elif health_score >= 75 and critical_issues <= 1:
        health_status = "good"
        description = "MySQL运行状况良好"
    elif health_score >= 60:
        health_status = "fair"
        description = "MySQL运行状况一般，需要关注"
    elif health_score >= 40:
        health_status = "poor"
        description = "MySQL运行状况较差，需要优化"
    else:
        health_status = "critical"
        description = "MySQL运行状况严重，需要立即处理"
    
    return {
        "status": health_status,
        "description": description,
        "health_score": health_score,
        "critical_issues": critical_issues
    }
