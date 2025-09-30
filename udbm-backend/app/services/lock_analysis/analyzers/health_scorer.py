"""
健康评分器

计算数据库锁性能的综合健康评分
"""
import logging
from typing import List, Dict, Any

from ..interfaces import IAnalyzer
from ..models import WaitChain, ContentionMetrics, LockStatistics
from ..factories import register_analyzer

logger = logging.getLogger(__name__)


@register_analyzer('health_score')
class LockHealthScorer(IAnalyzer):
    """
    锁健康评分器
    
    使用加权多维度评分模型计算健康评分（0-100）
    """
    
    # 各维度权重
    WEIGHTS = {
        'wait_time': 0.30,      # 等待时间
        'contention': 0.25,     # 竞争程度
        'deadlock': 0.20,       # 死锁频率
        'blocking_chain': 0.15, # 阻塞链
        'timeout': 0.10         # 超时频率
    }
    
    def get_name(self) -> str:
        """获取分析器名称"""
        return "LockHealthScorer"
    
    async def analyze(
        self,
        chains: List[WaitChain],
        contentions: List[ContentionMetrics],
        statistics: LockStatistics
    ) -> float:
        """
        计算健康评分
        
        Args:
            chains: 等待链列表
            contentions: 竞争指标列表
            statistics: 锁统计信息
            
        Returns:
            float: 健康评分 (0-100)
        """
        # 1. 等待时间评分
        wait_score = self._score_wait_time(contentions)
        
        # 2. 竞争评分
        contention_score = self._score_contention(contentions)
        
        # 3. 死锁评分
        deadlock_score = self._score_deadlock(statistics.deadlock_count, chains)
        
        # 4. 阻塞链评分
        chain_score = self._score_blocking_chains(chains)
        
        # 5. 超时评分
        timeout_score = self._score_timeout(statistics.timeout_count)
        
        # 加权平均
        final_score = (
            wait_score * self.WEIGHTS['wait_time'] +
            contention_score * self.WEIGHTS['contention'] +
            deadlock_score * self.WEIGHTS['deadlock'] +
            chain_score * self.WEIGHTS['blocking_chain'] +
            timeout_score * self.WEIGHTS['timeout']
        )
        
        # 确保在0-100范围内
        final_score = max(0.0, min(100.0, final_score))
        
        logger.info(
            f"Health score calculated: {final_score:.2f} "
            f"(wait:{wait_score:.1f}, cont:{contention_score:.1f}, "
            f"dead:{deadlock_score:.1f}, chain:{chain_score:.1f}, "
            f"timeout:{timeout_score:.1f})"
        )
        
        return round(final_score, 2)
    
    def _score_wait_time(self, contentions: List[ContentionMetrics]) -> float:
        """
        等待时间评分
        
        Args:
            contentions: 竞争指标列表
            
        Returns:
            float: 评分 (0-100)
        """
        if not contentions:
            return 100.0
        
        # 计算平均等待时间
        avg_wait = sum(c.avg_wait_time for c in contentions) / len(contentions)
        
        # 使用逆S曲线映射
        # 优秀: <100ms -> 90-100分
        # 良好: 100ms-500ms -> 70-90分
        # 一般: 500ms-2s -> 50-70分
        # 较差: 2s-5s -> 30-50分
        # 很差: >5s -> 0-30分
        
        if avg_wait < 0.1:  # <100ms
            return 95 + (0.1 - avg_wait) * 50
        elif avg_wait < 0.5:  # 100-500ms
            return 70 + (0.5 - avg_wait) / 0.4 * 25
        elif avg_wait < 2.0:  # 500ms-2s
            return 50 + (2.0 - avg_wait) / 1.5 * 20
        elif avg_wait < 5.0:  # 2s-5s
            return 30 + (5.0 - avg_wait) / 3.0 * 20
        else:  # >5s
            return max(0, 30 - (avg_wait - 5.0) * 5)
    
    def _score_contention(self, contentions: List[ContentionMetrics]) -> float:
        """
        竞争评分
        
        Args:
            contentions: 竞争指标列表
            
        Returns:
            float: 评分 (0-100)
        """
        if not contentions:
            return 100.0
        
        # 统计不同模式的竞争
        hot_spots = sum(1 for c in contentions if c.pattern == "hot_spot")
        bursts = sum(1 for c in contentions if c.pattern == "burst")
        frequent = sum(1 for c in contentions if c.pattern == "frequent")
        
        # 基础分数
        score = 100.0
        
        # 热点竞争扣分最多
        if hot_spots > 5:
            score -= 40
        elif hot_spots > 2:
            score -= 30
        elif hot_spots > 0:
            score -= 20
        
        # 突发竞争扣分
        if bursts > 3:
            score -= 20
        elif bursts > 0:
            score -= 10
        
        # 频繁竞争扣分
        if frequent > 5:
            score -= 15
        elif frequent > 2:
            score -= 10
        
        return max(0.0, score)
    
    def _score_deadlock(
        self,
        deadlock_count: int,
        chains: List[WaitChain]
    ) -> float:
        """
        死锁评分
        
        Args:
            deadlock_count: 死锁次数（来自统计）
            chains: 等待链列表（检查当前死锁）
            
        Returns:
            float: 评分 (0-100)
        """
        # 检查当前死锁
        current_deadlocks = sum(1 for c in chains if c.is_cycle)
        
        # 如果当前有死锁，严重扣分
        if current_deadlocks > 0:
            return 20.0
        
        # 根据历史死锁次数评分
        if deadlock_count == 0:
            return 100.0
        elif deadlock_count <= 2:
            return 80.0
        elif deadlock_count <= 5:
            return 60.0
        elif deadlock_count <= 10:
            return 40.0
        else:
            return 20.0
    
    def _score_blocking_chains(self, chains: List[WaitChain]) -> float:
        """
        阻塞链评分
        
        Args:
            chains: 等待链列表
            
        Returns:
            float: 评分 (0-100)
        """
        if not chains:
            return 100.0
        
        # 统计不同严重程度的链
        critical = sum(1 for c in chains if c.severity == "critical")
        high = sum(1 for c in chains if c.severity == "high")
        medium = sum(1 for c in chains if c.severity == "medium")
        
        # 基础分数
        score = 100.0
        
        # 严重链扣分
        if critical > 3:
            score -= 50
        elif critical > 1:
            score -= 35
        elif critical > 0:
            score -= 25
        
        # 高优先级链扣分
        if high > 5:
            score -= 20
        elif high > 2:
            score -= 15
        elif high > 0:
            score -= 10
        
        # 中等优先级链扣分
        if medium > 10:
            score -= 10
        elif medium > 5:
            score -= 5
        
        return max(0.0, score)
    
    def _score_timeout(self, timeout_count: int) -> float:
        """
        超时评分
        
        Args:
            timeout_count: 超时次数
            
        Returns:
            float: 评分 (0-100)
        """
        if timeout_count == 0:
            return 100.0
        elif timeout_count <= 5:
            return 85.0
        elif timeout_count <= 10:
            return 70.0
        elif timeout_count <= 20:
            return 50.0
        else:
            return 30.0