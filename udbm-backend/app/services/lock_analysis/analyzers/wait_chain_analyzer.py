"""
等待链分析器

分析锁等待链，识别死锁和长时间等待
"""
import logging
from typing import List, Dict, Any

from ..interfaces import IAnalyzer
from ..models import WaitChain
from ..factories import register_analyzer

logger = logging.getLogger(__name__)


@register_analyzer('wait_chain')
class WaitChainAnalyzer(IAnalyzer):
    """
    等待链分析器
    
    职责：
    1. 分析等待链的特征
    2. 识别死锁和潜在死锁
    3. 评估等待链的影响
    4. 生成解决建议
    """
    
    def get_name(self) -> str:
        """获取分析器名称"""
        return "WaitChainAnalyzer"
    
    async def analyze(self, chains: List[WaitChain]) -> Dict[str, Any]:
        """
        分析等待链
        
        Args:
            chains: 等待链列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        if not chains:
            return {
                "total_chains": 0,
                "critical_chains": 0,
                "high_chains": 0,
                "medium_chains": 0,
                "low_chains": 0,
                "avg_chain_length": 0.0,
                "max_chain_length": 0,
                "avg_wait_time": 0.0,
                "max_wait_time": 0.0,
                "has_deadlock": False,
                "deadlock_count": 0,
                "long_wait_chains": [],
                "chains": []
            }
        
        # 统计不同严重程度的等待链
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for chain in chains:
            severity_counts[chain.severity] = severity_counts.get(chain.severity, 0) + 1
        
        # 计算统计指标
        total_chains = len(chains)
        avg_length = sum(c.chain_length for c in chains) / total_chains
        max_length = max(c.chain_length for c in chains)
        avg_wait = sum(c.total_wait_time for c in chains) / total_chains
        max_wait = max(c.total_wait_time for c in chains)
        
        # 识别死锁
        deadlocks = [c for c in chains if c.is_cycle]
        has_deadlock = len(deadlocks) > 0
        
        # 识别长时间等待
        long_wait_threshold = 10.0  # 10秒
        long_wait_chains = [
            c for c in chains 
            if c.total_wait_time >= long_wait_threshold
        ]
        
        # 生成分析报告
        result = {
            "total_chains": total_chains,
            "critical_chains": severity_counts["critical"],
            "high_chains": severity_counts["high"],
            "medium_chains": severity_counts["medium"],
            "low_chains": severity_counts["low"],
            "avg_chain_length": round(avg_length, 2),
            "max_chain_length": max_length,
            "avg_wait_time": round(avg_wait, 2),
            "max_wait_time": round(max_wait, 2),
            "has_deadlock": has_deadlock,
            "deadlock_count": len(deadlocks),
            "long_wait_count": len(long_wait_chains),
            "long_wait_chains": [c.to_dict() for c in long_wait_chains[:5]],  # 只返回前5个
            "chains": chains,
            "analysis": self._generate_analysis_text(
                total_chains, severity_counts, has_deadlock, len(long_wait_chains)
            ),
            "recommendations": self._generate_recommendations(
                severity_counts, has_deadlock, long_wait_chains
            )
        }
        
        logger.info(
            f"Wait chain analysis: {total_chains} chains, "
            f"{severity_counts['critical']} critical, "
            f"{len(deadlocks)} deadlocks"
        )
        
        return result
    
    def _generate_analysis_text(
        self,
        total: int,
        severity_counts: Dict[str, int],
        has_deadlock: bool,
        long_wait_count: int
    ) -> str:
        """
        生成分析文本
        
        Args:
            total: 总等待链数
            severity_counts: 严重程度统计
            has_deadlock: 是否有死锁
            long_wait_count: 长时间等待数量
            
        Returns:
            str: 分析文本
        """
        if total == 0:
            return "当前没有检测到锁等待链，系统运行正常。"
        
        texts = []
        
        texts.append(f"检测到{total}个锁等待链。")
        
        if has_deadlock:
            texts.append("⚠️ 发现死锁！需要立即处理。")
        
        if severity_counts["critical"] > 0:
            texts.append(f"其中{severity_counts['critical']}个为严重等待链，需要优先处理。")
        
        if long_wait_count > 0:
            texts.append(f"有{long_wait_count}个等待链等待时间超过10秒。")
        
        return " ".join(texts)
    
    def _generate_recommendations(
        self,
        severity_counts: Dict[str, int],
        has_deadlock: bool,
        long_wait_chains: List[WaitChain]
    ) -> List[str]:
        """
        生成优化建议
        
        Args:
            severity_counts: 严重程度统计
            has_deadlock: 是否有死锁
            long_wait_chains: 长时间等待链列表
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        if has_deadlock:
            recommendations.append("立即检查死锁涉及的查询，优化事务逻辑以避免死锁")
            recommendations.append("考虑调整事务隔离级别或锁获取顺序")
        
        if severity_counts["critical"] > 0:
            recommendations.append("检查严重等待链涉及的查询执行计划")
            recommendations.append("考虑添加适当的索引以减少锁持有时间")
        
        if len(long_wait_chains) > 0:
            recommendations.append("优化长时间运行的查询，减少事务持续时间")
            recommendations.append("考虑拆分大事务为多个小事务")
        
        if severity_counts["high"] + severity_counts["critical"] > 3:
            recommendations.append("系统锁竞争较严重，建议全面review数据库访问模式")
            recommendations.append("考虑使用乐观锁替代悲观锁")
        
        return recommendations