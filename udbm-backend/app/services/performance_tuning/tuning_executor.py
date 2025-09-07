"""
调优执行器
负责执行各种调优任务，如创建索引、重写查询等
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.performance_tuning import TuningTask, IndexSuggestion
from app.models.database import DatabaseInstance

logger = logging.getLogger(__name__)


class TuningExecutor:
    """调优执行器"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def execute_index_creation(self, task: TuningTask) -> Dict[str, Any]:
        """
        执行索引创建任务
        """
        try:
            task_config = json.loads(task.task_config)
            execution_sql = task.execution_sql

            # Mock 执行结果
            execution_result = {
                "success": True,
                "execution_time": 0.15,
                "index_name": task_config.get("index_name", "idx_unknown"),
                "table_name": task_config.get("table_name", "unknown_table"),
                "columns": task_config.get("columns", []),
                "index_type": task_config.get("index_type", "btree"),
                "estimated_size_mb": 25.6,
                "message": f"索引 {task_config.get('index_name')} 创建成功"
            }

            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.execution_result = json.dumps(execution_result)

            self.db.commit()

            return execution_result

        except Exception as e:
            logger.error(f"索引创建失败: {str(e)}")

            # 更新任务状态为失败
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            self.db.commit()

            return {
                "success": False,
                "error": str(e),
                "message": "索引创建失败"
            }

    def execute_query_rewrite(self, task: TuningTask) -> Dict[str, Any]:
        """
        执行查询重写任务
        """
        try:
            task_config = json.loads(task.task_config)
            original_query = task_config.get("original_query", "")
            rewritten_query = task_config.get("rewritten_query", "")

            # Mock 执行验证
            validation_result = {
                "original_query": original_query,
                "rewritten_query": rewritten_query,
                "performance_improvement": {
                    "estimated_speedup": 2.3,
                    "estimated_reduction_percent": 57
                },
                "validation": {
                    "syntax_check": True,
                    "semantic_equivalence": True,
                    "performance_test": True
                }
            }

            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.execution_result = json.dumps(validation_result)

            self.db.commit()

            return validation_result

        except Exception as e:
            logger.error(f"查询重写失败: {str(e)}")

            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            self.db.commit()

            return {
                "success": False,
                "error": str(e),
                "message": "查询重写失败"
            }

    def execute_config_tuning(self, task: TuningTask) -> Dict[str, Any]:
        """
        执行配置调优任务
        """
        try:
            task_config = json.loads(task.task_config)
            config_changes = task_config.get("changes", [])

            # Mock 配置变更结果
            result = {
                "config_changes": config_changes,
                "applied_changes": [],
                "validation_results": [],
                "restart_required": False,
                "estimated_improvement": {
                    "performance_gain_percent": 15,
                    "memory_usage_change_mb": -256
                }
            }

            for change in config_changes:
                applied_change = {
                    "parameter": change["parameter"],
                    "old_value": change["old_value"],
                    "new_value": change["new_value"],
                    "applied": True,
                    "restart_required": change.get("restart_required", False)
                }
                result["applied_changes"].append(applied_change)

                if applied_change["restart_required"]:
                    result["restart_required"] = True

            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.execution_result = json.dumps(result)

            self.db.commit()

            return result

        except Exception as e:
            logger.error(f"配置调优失败: {str(e)}")

            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            self.db.commit()

            return {
                "success": False,
                "error": str(e),
                "message": "配置调优失败"
            }

    def execute_vacuum(self, task: TuningTask) -> Dict[str, Any]:
        """
        执行VACUUM任务
        """
        try:
            task_config = json.loads(task.task_config)
            vacuum_sql = task.execution_sql

            # Mock 执行结果
            execution_result = {
                "success": True,
                "execution_time": 45.6,
                "vacuum_type": task_config.get("vacuum_type", "VACUUM"),
                "table_name": task_config.get("table_name", ""),
                "pages_removed": 1250,
                "pages_remain": 8750,
                "tuples_removed": 50000,
                "tuples_remain": 350000,
                "message": f"{task_config.get('vacuum_type')} 操作成功完成"
            }

            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.execution_result = json.dumps(execution_result)

            self.db.commit()

            return execution_result

        except Exception as e:
            logger.error(f"VACUUM执行失败: {str(e)}")

            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            self.db.commit()

            return {
                "success": False,
                "error": str(e),
                "message": "VACUUM执行失败"
            }

    def execute_analyze(self, task: TuningTask) -> Dict[str, Any]:
        """
        执行ANALYZE任务
        """
        try:
            task_config = json.loads(task.task_config)
            analyze_sql = task.execution_sql

            # Mock 执行结果
            execution_result = {
                "success": True,
                "execution_time": 12.3,
                "table_name": task_config.get("table_name", ""),
                "statistics_updated": True,
                "estimated_rows_updated": True,
                "message": f"表 {task_config.get('table_name')} 统计信息更新完成"
            }

            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.execution_result = json.dumps(execution_result)

            self.db.commit()

            return execution_result

        except Exception as e:
            logger.error(f"ANALYZE执行失败: {str(e)}")

            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            self.db.commit()

            return {
                "success": False,
                "error": str(e),
                "message": "ANALYZE执行失败"
            }

    def execute_reindex(self, task: TuningTask) -> Dict[str, Any]:
        """
        执行REINDEX任务
        """
        try:
            task_config = json.loads(task.task_config)
            reindex_sql = task.execution_sql

            # Mock 执行结果
            execution_result = {
                "success": True,
                "execution_time": 89.7,
                "index_name": task_config.get("index_name", ""),
                "index_rebuilt": True,
                "size_before": "256MB",
                "size_after": "245MB",
                "message": f"索引 {task_config.get('index_name')} 重建完成"
            }

            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.execution_result = json.dumps(execution_result)

            self.db.commit()

            return execution_result

        except Exception as e:
            logger.error(f"REINDEX执行失败: {str(e)}")

            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            self.db.commit()

            return {
                "success": False,
                "error": str(e),
                "message": "REINDEX执行失败"
            }

    def create_index_suggestion_task(self, suggestion: IndexSuggestion) -> TuningTask:
        """
        为索引建议创建调优任务
        """
        task_config = {
            "table_name": suggestion.table_name,
            "columns": json.loads(suggestion.column_names),
            "index_type": suggestion.index_type,
            "index_name": f"idx_{suggestion.table_name}_{'_'.join(json.loads(suggestion.column_names))}",
            "reason": suggestion.reason,
            "estimated_improvement": suggestion.estimated_improvement
        }

        execution_sql = self._generate_index_creation_sql(task_config)

        task = TuningTask(
            database_id=suggestion.database_id,
            task_type="index_creation",
            task_name=f"为表 {suggestion.table_name} 创建索引",
            description=f"创建索引以优化查询性能，预计提升: {suggestion.estimated_improvement}",
            task_config=json.dumps(task_config),
            execution_sql=execution_sql,
            priority=self._calculate_task_priority(suggestion),
            related_suggestion_id=suggestion.id
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def create_query_rewrite_task(self, database_id: int, original_query: str, rewritten_query: str) -> TuningTask:
        """
        创建查询重写任务
        """
        task_config = {
            "original_query": original_query,
            "rewritten_query": rewritten_query,
            "analysis": {
                "original_complexity": "medium",
                "rewritten_complexity": "low",
                "estimated_improvement": "60% faster"
            }
        }

        task = TuningTask(
            database_id=database_id,
            task_type="query_rewrite",
            task_name="查询重写优化",
            description="重写低效查询以提升性能",
            task_config=json.dumps(task_config),
            priority=2
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def create_config_tuning_task(self, database_id: int, config_changes: List[Dict]) -> TuningTask:
        """
        创建配置调优任务
        """
        task_config = {
            "changes": config_changes,
            "backup_required": True,
            "validation_required": True
        }

        task = TuningTask(
            database_id=database_id,
            task_type="config_tuning",
            task_name="数据库配置优化",
            description=f"调整 {len(config_changes)} 个配置参数",
            task_config=json.dumps(task_config),
            priority=3
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def create_vacuum_task(self, database_id: int, table_name: str, vacuum_type: str = "VACUUM") -> TuningTask:
        """
        创建VACUUM任务
        """
        task_config = {
            "table_name": table_name,
            "vacuum_type": vacuum_type,  # VACUUM, VACUUM FULL, VACUUM ANALYZE
            "estimated_duration": "30-300秒"  # 取决于表大小
        }

        vacuum_sql = self._generate_vacuum_sql(task_config)

        task = TuningTask(
            database_id=database_id,
            task_type="vacuum",
            task_name=f"{vacuum_type} 表 {table_name}",
            description=f"执行 {vacuum_type} 操作清理表 {table_name} 的死元组",
            task_config=json.dumps(task_config),
            execution_sql=vacuum_sql,
            priority=4  # VACUUM优先级较低
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def create_analyze_task(self, database_id: int, table_name: str) -> TuningTask:
        """
        创建ANALYZE任务
        """
        task_config = {
            "table_name": table_name,
            "analyze_type": "ANALYZE",
            "estimated_duration": "10-60秒"
        }

        analyze_sql = f"ANALYZE {table_name};"

        task = TuningTask(
            database_id=database_id,
            task_type="analyze",
            task_name=f"分析表 {table_name} 统计信息",
            description=f"更新表 {table_name} 的统计信息以优化查询计划",
            task_config=json.dumps(task_config),
            execution_sql=analyze_sql,
            priority=3
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def create_reindex_task(self, database_id: int, index_name: str) -> TuningTask:
        """
        创建REINDEX任务
        """
        task_config = {
            "index_name": index_name,
            "reindex_type": "REINDEX",
            "estimated_duration": "60-600秒"  # 取决于索引大小
        }

        reindex_sql = f"REINDEX INDEX CONCURRENTLY {index_name};"

        task = TuningTask(
            database_id=database_id,
            task_type="reindex",
            task_name=f"重建索引 {index_name}",
            description=f"重建索引 {index_name} 以优化性能",
            task_config=json.dumps(task_config),
            execution_sql=reindex_sql,
            priority=5  # REINDEX优先级较高
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def execute_task(self, task_id: int) -> Dict[str, Any]:
        """
        执行指定任务
        """
        task = self.db.query(TuningTask).filter(TuningTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "任务不存在"}

        if task.status not in ["pending", "failed"]:
            return {"success": False, "error": f"任务状态为 {task.status}，无法执行"}

        # 更新任务状态为运行中
        task.status = "running"
        task.started_at = datetime.now()
        self.db.commit()

        # 根据任务类型执行相应操作
        if task.task_type == "index_creation":
            return self.execute_index_creation(task)
        elif task.task_type == "query_rewrite":
            return self.execute_query_rewrite(task)
        elif task.task_type == "config_tuning":
            return self.execute_config_tuning(task)
        elif task.task_type == "vacuum":
            return self.execute_vacuum(task)
        elif task.task_type == "analyze":
            return self.execute_analyze(task)
        elif task.task_type == "reindex":
            return self.execute_reindex(task)
        else:
            task.status = "failed"
            task.error_message = f"不支持的任务类型: {task.task_type}"
            self.db.commit()
            return {"success": False, "error": f"不支持的任务类型: {task.task_type}"}

    def get_task_status(self, task_id: int) -> Optional[TuningTask]:
        """
        获取任务状态
        """
        return self.db.query(TuningTask).filter(TuningTask.id == task_id).first()

    def get_pending_tasks(self, database_id: Optional[int] = None) -> List[TuningTask]:
        """
        获取待执行的任务
        """
        query = self.db.query(TuningTask).filter(TuningTask.status == "pending")
        if database_id:
            query = query.filter(TuningTask.database_id == database_id)

        return query.order_by(TuningTask.priority.desc(), TuningTask.created_at).all()

    def cancel_task(self, task_id: int) -> Dict[str, Any]:
        """
        取消任务
        """
        task = self.db.query(TuningTask).filter(TuningTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "任务不存在"}

        if task.status not in ["pending", "running"]:
            return {"success": False, "error": f"任务状态为 {task.status}，无法取消"}

        task.status = "cancelled"
        if task.status == "running":
            task.completed_at = datetime.now()
        self.db.commit()

        return {"success": True, "message": "任务已取消"}

    def _generate_index_creation_sql(self, task_config: Dict[str, Any]) -> str:
        """
        生成PostgreSQL索引创建SQL
        """
        table_name = task_config["table_name"]
        columns = task_config["columns"]
        index_name = task_config["index_name"]
        index_type = task_config.get("index_type", "btree")

        # PostgreSQL支持的索引类型
        if index_type == "btree":
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} ({', '.join(columns)});"
        elif index_type == "hash":
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING hash ({', '.join(columns)});"
        elif index_type == "gin":
            # GIN索引通常用于数组、JSON、全文搜索
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING gin ({', '.join(columns)});"
        elif index_type == "gist":
            # GiST索引用于几何数据、范围查询等
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING gist ({', '.join(columns)});"
        elif index_type == "spgist":
            # SP-GiST索引用于空间分区
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING spgist ({', '.join(columns)});"
        elif index_type == "brin":
            # BRIN索引用于有序数据的范围查询
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING brin ({', '.join(columns)});"
        elif index_type == "gin_trgm":
            # 全文搜索索引（使用pg_trgm扩展）
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING gin ({', '.join(columns)} gin_trgm_ops);"
        elif index_type == "fulltext":
            # 全文搜索索引
            column_name = columns[0] if columns else "text_column"
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING gin(to_tsvector('english', {column_name}));"
        else:
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} ({', '.join(columns)});"

    def _generate_vacuum_sql(self, task_config: Dict[str, Any]) -> str:
        """
        生成VACUUM SQL语句
        """
        table_name = task_config["table_name"]
        vacuum_type = task_config.get("vacuum_type", "VACUUM")

        if vacuum_type == "VACUUM FULL":
            return f"VACUUM FULL {table_name};"
        elif vacuum_type == "VACUUM ANALYZE":
            return f"VACUUM ANALYZE {table_name};"
        elif vacuum_type == "VACUUM FREEZE":
            return f"VACUUM FREEZE {table_name};"
        else:
            return f"VACUUM {table_name};"

    def _calculate_task_priority(self, suggestion: IndexSuggestion) -> int:
        """
        计算任务优先级
        """
        priority = 1  # 默认优先级

        # 根据影响评分调整优先级
        if suggestion.impact_score >= 80:
            priority = 5
        elif suggestion.impact_score >= 60:
            priority = 4
        elif suggestion.impact_score >= 40:
            priority = 3
        elif suggestion.impact_score >= 20:
            priority = 2

        return priority

    def get_task_statistics(self, database_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取任务统计信息
        """
        query = self.db.query(TuningTask)
        if database_id:
            query = query.filter(TuningTask.database_id == database_id)

        total_tasks = query.count()
        completed_tasks = query.filter(TuningTask.status == "completed").count()
        failed_tasks = query.filter(TuningTask.status == "failed").count()
        pending_tasks = query.filter(TuningTask.status == "pending").count()
        running_tasks = query.filter(TuningTask.status == "running").count()

        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "pending": pending_tasks,
            "running": running_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
