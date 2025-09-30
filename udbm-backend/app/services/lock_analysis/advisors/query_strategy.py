"""
查询优化策略

为长时间阻塞的查询生成优化建议
"""
import logging
from typing import List

from ..interfaces import IOptimizationStrategy
from ..models import AnalysisResult, OptimizationAdvice
from ..factories import register_strategy

logger = logging.getLogger(__name__)


@register_strategy('query')
class QueryOptimizationStrategy(IOptimizationStrategy):
    """
    查询优化策略
    
    适用场景：
    1. 长时间等待链
    2. 查询执行时间过长
    3. 锁持有时间过长
    """
    
    def get_priority(self) -> int:
        """获取策略优先级"""
        return 2  # 中高优先级
    
    def is_applicable(self, analysis: AnalysisResult) -> bool:
        """
        判断策略是否适用
        
        Args:
            analysis: 分析结果
            
        Returns:
            bool: 是否适用
        """
        # 如果存在长时间等待链，则适用
        long_chains = [
            c for c in analysis.wait_chains 
            if c.total_wait_time > 5.0
        ]
        
        return len(long_chains) > 0
    
    async def generate(self, analysis: AnalysisResult) -> List[OptimizationAdvice]:
        """
        生成查询优化建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            List[OptimizationAdvice]: 优化建议列表
        """
        advice_list = []
        
        # 识别长时间等待链
        long_chains = [
            c for c in analysis.wait_chains 
            if c.total_wait_time > 5.0
        ]
        
        # 为前2个长等待链生成建议
        for i, chain in enumerate(long_chains[:2], 1):
            blocking_query = chain.get_blocking_query()
            
            advice = OptimizationAdvice(
                advice_id=f"query_opt_{analysis.database_id}_{i}",
                type="query",
                priority="critical" if chain.severity == "critical" else "high",
                title=f"优化长时间阻塞查询 (链ID: {chain.chain_id})",
                description=(
                    f"检测到查询导致长时间阻塞。\n"
                    f"等待时间: {chain.total_wait_time:.2f}秒, "
                    f"链长度: {chain.chain_length}, "
                    f"严重程度: {chain.severity}\n"
                    f"{'⚠️ 检测到死锁！' if chain.is_cycle else ''}"
                ),
                object_name=None,
                impact_score=min(100, chain.total_wait_time * 10),
                sql_script=self._generate_query_optimization_guide(blocking_query),
                rollback_script=None,
                estimated_improvement="预计减少阻塞时间 40-60%",
                actions=[
                    "1. 使用 EXPLAIN ANALYZE 分析查询执行计划",
                    "2. 检查是否缺少适当的索引",
                    "3. 考虑重写查询以减少锁持有时间",
                    "4. 使用更细粒度的锁（如行级锁代替表锁）",
                    "5. 拆分大事务为多个小事务",
                    "6. 调整事务隔离级别（如使用READ COMMITTED）",
                    f"7. 问题查询: {blocking_query[:100] if blocking_query else 'N/A'}..."
                ]
            )
            advice_list.append(advice)
        
        # 如果健康评分很低，添加系统级建议
        if analysis.health_score < 50:
            advice = OptimizationAdvice(
                advice_id=f"query_sys_{analysis.database_id}",
                type="query",
                priority="critical",
                title="系统锁性能严重问题 - 需要全面优化",
                description=(
                    f"当前锁健康评分: {analysis.health_score:.1f}/100，系统存在严重的锁性能问题。\n"
                    f"等待链数量: {len(analysis.wait_chains)}, "
                    f"竞争对象: {len(analysis.contentions)}, "
                    f"死锁次数: {analysis.statistics.deadlock_count}"
                ),
                object_name=None,
                impact_score=100.0,
                sql_script=None,
                rollback_script=None,
                estimated_improvement="预计整体性能提升 50%+",
                actions=[
                    "1. 全面审查数据库访问模式和事务设计",
                    "2. 识别并优化所有慢查询",
                    "3. 考虑使用乐观锁替代悲观锁",
                    "4. 实施读写分离架构",
                    "5. 考虑分库分表或分区表",
                    "6. 优化应用层并发控制逻辑",
                    "7. 调整数据库连接池和锁相关参数"
                ]
            )
            advice_list.append(advice)
        
        logger.info(f"Generated {len(advice_list)} query optimization advices")
        
        return advice_list
    
    def _generate_query_optimization_guide(self, query: str) -> str:
        """
        生成查询优化指南
        
        Args:
            query: 查询语句
            
        Returns:
            str: 优化指南
        """
        return f"""-- 查询优化指南

-- 1. 分析当前查询执行计划
EXPLAIN (ANALYZE, BUFFERS) 
{query if query else '-- 原始查询'};

-- 2. 查看表统计信息
-- PostgreSQL:
SELECT 
    schemaname, tablename, 
    n_live_tup, n_dead_tup,
    last_vacuum, last_analyze
FROM pg_stat_user_tables
WHERE tablename IN (
    -- 提取查询涉及的表名
);

-- 3. 检查表大小和索引
-- PostgreSQL:
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public';

-- 4. 优化建议：
-- - 如果是全表扫描，考虑添加索引
-- - 如果是JOIN操作，确保JOIN列有索引
-- - 如果是子查询，考虑改写为JOIN
-- - 如果是ORDER BY/GROUP BY，考虑相应的索引
-- - 如果锁定大量行，考虑分批处理

-- 5. 事务优化：
-- - 减少事务中的操作数量
-- - 避免在事务中执行耗时操作
-- - 使用合适的隔离级别
-- - 考虑使用SELECT ... FOR UPDATE SKIP LOCKED

-- 6. 监控查询性能：
-- PostgreSQL:
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%关键字%'
ORDER BY total_time DESC
LIMIT 10;
"""