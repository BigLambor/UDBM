"""
索引优化策略

为热点竞争对象生成索引优化建议
"""
import logging
from typing import List
from datetime import datetime

from ..interfaces import IOptimizationStrategy
from ..models import AnalysisResult, OptimizationAdvice
from ..factories import register_strategy

logger = logging.getLogger(__name__)


@register_strategy('index')
class IndexOptimizationStrategy(IOptimizationStrategy):
    """
    索引优化策略
    
    适用场景：
    1. 热点表竞争严重
    2. 锁等待时间较长
    3. 查询缺少适当索引
    """
    
    def get_priority(self) -> int:
        """获取策略优先级"""
        return 1  # 高优先级
    
    def is_applicable(self, analysis: AnalysisResult) -> bool:
        """
        判断策略是否适用
        
        Args:
            analysis: 分析结果
            
        Returns:
            bool: 是否适用
        """
        # 如果存在热点竞争，则适用
        hot_spots = [
            c for c in analysis.contentions 
            if c.pattern == "hot_spot"
        ]
        
        return len(hot_spots) > 0
    
    async def generate(self, analysis: AnalysisResult) -> List[OptimizationAdvice]:
        """
        生成索引优化建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            List[OptimizationAdvice]: 优化建议列表
        """
        advice_list = []
        
        # 识别热点对象
        hot_spots = [
            c for c in analysis.contentions 
            if c.pattern in ["hot_spot", "frequent"]
        ]
        
        # 为前3个热点对象生成建议
        for i, contention in enumerate(hot_spots[:3], 1):
            advice = OptimizationAdvice(
                advice_id=f"idx_opt_{analysis.database_id}_{i}",
                type="index",
                priority="high" if contention.pattern == "hot_spot" else "medium",
                title=f"为热点表 {contention.object_name} 优化索引",
                description=(
                    f"检测到表 {contention.object_name} 存在{'严重' if contention.pattern == 'hot_spot' else '频繁'}的锁竞争。\n"
                    f"竞争次数: {contention.contention_count}, "
                    f"平均等待时间: {contention.avg_wait_time:.2f}秒, "
                    f"影响会话数: {contention.affected_sessions}"
                ),
                object_name=contention.object_name,
                impact_score=self._calculate_impact(contention),
                sql_script=self._generate_index_sql(contention.object_name, analysis.database_id),
                rollback_script=self._generate_rollback_sql(contention.object_name),
                estimated_improvement="预计减少锁等待时间 30-50%",
                actions=[
                    "1. 使用 EXPLAIN ANALYZE 分析相关查询的执行计划",
                    "2. 识别缺失的索引或索引使用不当的情况",
                    "3. 在非高峰期创建索引（使用CONCURRENTLY选项避免锁表）",
                    "4. 创建后监控索引效果和资源消耗",
                    "5. 考虑使用部分索引或表达式索引优化特定查询"
                ]
            )
            advice_list.append(advice)
        
        logger.info(f"Generated {len(advice_list)} index optimization advices")
        
        return advice_list
    
    def _calculate_impact(self, contention) -> float:
        """
        计算影响分数
        
        Args:
            contention: 竞争指标
            
        Returns:
            float: 影响分数 (0-100)
        """
        # 基于竞争次数和等待时间计算
        score = min(100, contention.contention_count * 2 + contention.total_wait_time)
        return round(score, 2)
    
    def _generate_index_sql(self, table_name: str, database_id: int) -> str:
        """
        生成索引SQL脚本
        
        Args:
            table_name: 表名
            database_id: 数据库ID
            
        Returns:
            str: SQL脚本
        """
        return f"""-- 索引优化脚本
-- 目标表: {table_name}
-- 数据库ID: {database_id}
-- 生成时间: {datetime.now().isoformat()}

-- 步骤1: 分析现有索引
-- PostgreSQL:
SELECT 
    schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename = '{table_name}';

-- MySQL:
-- SHOW INDEX FROM {table_name};

-- 步骤2: 分析表的查询模式
-- PostgreSQL:
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE query LIKE '%{table_name}%'
ORDER BY total_time DESC
LIMIT 10;

-- 步骤3: 创建建议的索引（需要根据实际查询模式调整）
-- PostgreSQL (CONCURRENTLY避免锁表):
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{table_name}_optimization
ON {table_name}(id, created_at)
WHERE deleted_at IS NULL;

-- MySQL:
-- CREATE INDEX idx_{table_name}_optimization ON {table_name}(id, created_at);

-- 步骤4: 更新统计信息
-- PostgreSQL:
ANALYZE {table_name};

-- MySQL:
-- ANALYZE TABLE {table_name};

-- 步骤5: 监控索引效果
-- PostgreSQL:
SELECT 
    schemaname, tablename, indexname, 
    idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = '{table_name}'
ORDER BY idx_scan DESC;
"""
    
    def _generate_rollback_sql(self, table_name: str) -> str:
        """
        生成回滚SQL脚本
        
        Args:
            table_name: 表名
            
        Returns:
            str: 回滚SQL
        """
        return f"""-- 回滚脚本
-- 如果索引效果不佳或影响写入性能，可以删除索引

-- PostgreSQL:
DROP INDEX CONCURRENTLY IF EXISTS idx_{table_name}_optimization;

-- MySQL:
-- DROP INDEX idx_{table_name}_optimization ON {table_name};
"""