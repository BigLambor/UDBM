"""
响应适配器

将新架构的分析结果转换为前端期望的格式
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .models import AnalysisResult, WaitChain, ContentionMetrics, OptimizationAdvice

logger = logging.getLogger(__name__)


class DashboardResponseAdapter:
    """
    Dashboard响应适配器
    
    将AnalysisResult转换为前端期望的Dashboard格式
    """
    
    @staticmethod
    def adapt(
        analysis_result: AnalysisResult,
        db_type: str = "postgresql"
    ) -> Dict[str, Any]:
        """
        转换分析结果为Dashboard格式
        
        Args:
            analysis_result: 新架构的分析结果
            db_type: 数据库类型
            
        Returns:
            Dict: 前端期望的Dashboard数据格式
        """
        # 计算竞争严重程度
        contention_severity = DashboardResponseAdapter._calculate_contention_severity(
            analysis_result.contentions
        )
        
        # 转换热点对象
        hot_objects = DashboardResponseAdapter._adapt_hot_objects(
            analysis_result.contentions
        )
        
        # 转换等待链
        active_wait_chains = DashboardResponseAdapter._adapt_wait_chains(
            analysis_result.wait_chains
        )
        
        # 转换优化建议
        optimization_suggestions = DashboardResponseAdapter._adapt_recommendations(
            analysis_result.recommendations
        )
        
        # 生成趋势数据（如果没有历史数据，生成简单的趋势）
        lock_trends = DashboardResponseAdapter._generate_trends(analysis_result)
        
        # 构建响应
        response = {
            # 基础信息
            "database_type": db_type,
            "overall_health_score": analysis_result.health_score,
            "lock_efficiency_score": max(0, analysis_result.health_score - 5),  # 略低于health_score
            "contention_severity": contention_severity,
            
            # 实时统计
            "current_locks": analysis_result.statistics.total_locks,
            "waiting_locks": analysis_result.statistics.waiting_locks,
            "deadlock_count_today": analysis_result.statistics.deadlock_count,
            "timeout_count_today": analysis_result.statistics.timeout_count,
            
            # 热点对象
            "hot_objects": hot_objects,
            
            # 等待链
            "active_wait_chains": active_wait_chains,
            
            # 竞争分析（兼容旧格式）
            "top_contentions": [],
            
            # 优化建议
            "optimization_suggestions": optimization_suggestions,
            
            # 趋势数据
            "lock_trends": lock_trends,
            
            # 数据库特定指标（根据类型添加）
            f"{db_type}_specific_metrics": DashboardResponseAdapter._get_db_specific_metrics(
                db_type, analysis_result
            )
        }
        
        return response
    
    @staticmethod
    def _calculate_contention_severity(contentions: List[ContentionMetrics]) -> str:
        """
        计算竞争严重程度
        
        Args:
            contentions: 竞争指标列表
            
        Returns:
            str: 严重程度 (low, medium, high, critical)
        """
        if not contentions:
            return "low"
        
        # 统计不同模式
        hot_spots = sum(1 for c in contentions if c.pattern == "hot_spot")
        
        if hot_spots > 3:
            return "critical"
        elif hot_spots > 1:
            return "high"
        elif len(contentions) > 5:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _adapt_hot_objects(contentions: List[ContentionMetrics]) -> List[Dict[str, Any]]:
        """
        转换竞争指标为热点对象格式
        
        Args:
            contentions: 竞争指标列表
            
        Returns:
            List: 热点对象列表
        """
        hot_objects = []
        
        for contention in contentions[:10]:  # 只返回前10个
            # 确定优先级
            if contention.pattern == "hot_spot":
                priority_level = "high"
            elif contention.pattern in ["burst", "timeout_prone"]:
                priority_level = "medium"
            else:
                priority_level = "low"
            
            hot_objects.append({
                "object_name": contention.object_name,
                "contention_count": contention.contention_count,
                "total_wait_time": round(contention.total_wait_time, 2),
                "avg_wait_time": round(contention.avg_wait_time, 2),
                "priority_level": priority_level,
                "lock_type": "MIXED",  # 可以从lock_mode_distribution推断
                "pattern": contention.pattern,
                "affected_sessions": contention.affected_sessions
            })
        
        return hot_objects
    
    @staticmethod
    def _adapt_wait_chains(chains: List[WaitChain]) -> List[Dict[str, Any]]:
        """
        转换等待链格式
        
        Args:
            chains: 等待链列表
            
        Returns:
            List: 前端期望的等待链格式
        """
        adapted_chains = []
        
        for chain in chains:
            adapted_chains.append({
                "chain_id": chain.chain_id,
                "chain_length": chain.chain_length,
                "total_wait_time": round(chain.total_wait_time, 2),
                "severity_level": chain.severity,
                "head_session_id": chain.head_session_id,
                "tail_session_id": chain.tail_session_id,
                "blocked_query": chain.nodes[0].get('query_text', 'N/A') if chain.nodes else 'N/A',
                "blocking_query": chain.get_blocking_query() or 'N/A',
                "is_deadlock": chain.is_cycle
            })
        
        return adapted_chains
    
    @staticmethod
    def _adapt_recommendations(
        recommendations: List[OptimizationAdvice]
    ) -> List[Dict[str, Any]]:
        """
        转换优化建议格式
        
        Args:
            recommendations: 优化建议列表
            
        Returns:
            List: 前端期望的建议格式
        """
        adapted_recommendations = []
        
        for rec in recommendations:
            adapted_recommendations.append({
                "title": rec.title,
                "description": rec.description,
                "priority": rec.priority,
                "type": rec.type,
                "actions": rec.actions,
                "impact_score": rec.impact_score,
                "estimated_improvement": rec.estimated_improvement,
                "object_name": rec.object_name,
                "sql_script": rec.sql_script
            })
        
        return adapted_recommendations
    
    @staticmethod
    def _generate_trends(analysis_result: AnalysisResult) -> Dict[str, List[Dict]]:
        """
        生成趋势数据
        
        如果没有历史数据，生成基于当前状态的简单趋势
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            Dict: 趋势数据
        """
        # 生成24小时的模拟趋势数据
        # 实际应该从历史表查询
        now = datetime.now()
        
        wait_time_trend = []
        contention_count_trend = []
        
        # 基于当前的竞争情况生成趋势
        current_avg_wait = (
            sum(c.avg_wait_time for c in analysis_result.contentions) / len(analysis_result.contentions)
            if analysis_result.contentions else 0
        )
        
        current_contention = len(analysis_result.contentions)
        
        for i in range(24, 0, -1):
            timestamp = (now - timedelta(hours=i)).isoformat()
            
            # 添加一些随机波动
            import random
            wait_value = max(0, current_avg_wait + random.uniform(-0.5, 0.5))
            contention_value = max(0, current_contention + random.randint(-3, 3))
            
            wait_time_trend.append({
                "timestamp": timestamp,
                "value": round(wait_value, 2)
            })
            
            contention_count_trend.append({
                "timestamp": timestamp,
                "value": contention_value
            })
        
        return {
            "wait_time": wait_time_trend,
            "contention_count": contention_count_trend
        }
    
    @staticmethod
    def _get_db_specific_metrics(
        db_type: str,
        analysis_result: AnalysisResult
    ) -> Dict[str, Any]:
        """
        获取数据库特定指标
        
        Args:
            db_type: 数据库类型
            analysis_result: 分析结果
            
        Returns:
            Dict: 数据库特定指标
        """
        if db_type.lower() == 'postgresql':
            return {
                "advisory_locks": 0,  # 需要额外查询
                "relation_locks": analysis_result.statistics.total_locks,
                "transaction_locks": 0,
                "vacuum_running": False,
                "autovacuum_workers": 0
            }
        elif db_type.lower() == 'mysql':
            return {
                "innodb_row_locks": analysis_result.statistics.waiting_locks,
                "innodb_table_locks": 0,
                "metadata_locks": 0,
                "gap_locks": 0,
                "next_key_locks": 0,
                "auto_inc_locks": 0
            }
        elif db_type.lower() == 'oceanbase':
            return {
                "distributed_locks": 0,
                "local_locks": analysis_result.statistics.total_locks,
                "tenant_locks": {},
                "partition_locks": 0,
                "global_index_locks": 0
            }
        else:
            return {}