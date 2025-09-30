"""
锁分析编排器

协调所有分析组件，执行完整的锁分析流程
"""
import logging
import asyncio
from typing import List, Optional
from datetime import timedelta, datetime

from .interfaces import ILockDataCollector, IAnalyzer, IOptimizationStrategy
from .models import AnalysisResult, LockStatistics
from .factories import AnalyzerRegistry, StrategyRegistry
from .cache import LockAnalysisCache

logger = logging.getLogger(__name__)


class LockAnalysisOrchestrator:
    """
    锁分析编排器
    
    职责：
    1. 协调数据采集、分析和建议生成
    2. 管理分析流程
    3. 处理并发和异常
    4. 缓存管理
    """
    
    def __init__(
        self,
        collector: ILockDataCollector,
        analyzers: Optional[List[IAnalyzer]] = None,
        strategies: Optional[List[IOptimizationStrategy]] = None,
        cache: Optional[LockAnalysisCache] = None
    ):
        """
        初始化编排器
        
        Args:
            collector: 数据采集器
            analyzers: 分析器列表（None则创建所有已注册的分析器）
            strategies: 优化策略列表（None则创建所有已注册的策略）
            cache: 缓存管理器
        """
        self.collector = collector
        self.analyzers = analyzers or self._create_default_analyzers()
        self.strategies = strategies or self._create_default_strategies()
        self.cache = cache
        
        logger.info(
            f"LockAnalysisOrchestrator initialized with "
            f"{len(self.analyzers)} analyzers and "
            f"{len(self.strategies)} strategies"
        )
    
    def _create_default_analyzers(self) -> List[IAnalyzer]:
        """创建默认分析器"""
        return AnalyzerRegistry.create_all_analyzers()
    
    def _create_default_strategies(self) -> List[IOptimizationStrategy]:
        """创建默认优化策略"""
        return StrategyRegistry.create_all_strategies()
    
    async def analyze_comprehensive(
        self,
        database_id: int,
        force_refresh: bool = False,
        duration: timedelta = timedelta(hours=1)
    ) -> AnalysisResult:
        """
        执行综合锁分析
        
        Args:
            database_id: 数据库ID
            force_refresh: 是否强制刷新（跳过缓存）
            duration: 统计时间范围
            
        Returns:
            AnalysisResult: 完整的分析结果
        """
        start_time = datetime.now()
        
        try:
            # 检查缓存
            if self.cache and not force_refresh:
                cache_key = f"lock_analysis:{database_id}:comprehensive"
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.info(f"返回缓存的分析结果: {database_id}")
                    return cached
            
            # 步骤1: 并行采集数据
            logger.info(f"开始采集数据库 {database_id} 的锁信息...")
            locks, chains, statistics = await asyncio.gather(
                self.collector.collect_current_locks(),
                self.collector.collect_wait_chains(),
                self.collector.collect_statistics(duration),
                return_exceptions=True
            )
            
            # 处理异常
            if isinstance(locks, Exception):
                logger.error(f"采集锁失败: {locks}")
                locks = []
            if isinstance(chains, Exception):
                logger.error(f"采集等待链失败: {chains}")
                chains = []
            if isinstance(statistics, Exception):
                logger.error(f"采集统计信息失败: {statistics}")
                statistics = LockStatistics(
                    database_id=database_id,
                    total_locks=0,
                    waiting_locks=0,
                    granted_locks=0,
                    deadlock_count=0,
                    timeout_count=0,
                    lock_type_distribution={}
                )
            
            logger.info(
                f"数据采集完成: {len(locks)} 锁, "
                f"{len(chains)} 等待链, "
                f"{statistics.total_locks} 总锁数"
            )
            
            # 步骤2: 执行分析
            logger.info("执行锁分析...")
            
            # 分析竞争
            contention_analyzer = next(
                (a for a in self.analyzers if a.get_name() == "ContentionAnalyzer"),
                None
            )
            contentions = []
            if contention_analyzer:
                contentions = await contention_analyzer.analyze(locks)
                logger.info(f"竞争分析完成: {len(contentions)} 个竞争对象")
            
            # 分析等待链
            chain_analyzer = next(
                (a for a in self.analyzers if a.get_name() == "WaitChainAnalyzer"),
                None
            )
            chain_analysis = {}
            if chain_analyzer:
                chain_analysis = await chain_analyzer.analyze(chains)
                logger.info(f"等待链分析完成: {chain_analysis.get('total_chains', 0)} 个链")
            
            # 计算健康评分
            health_scorer = next(
                (a for a in self.analyzers if a.get_name() == "LockHealthScorer"),
                None
            )
            health_score = 100.0
            if health_scorer:
                health_score = await health_scorer.analyze(chains, contentions, statistics)
                logger.info(f"健康评分计算完成: {health_score:.2f}")
            
            # 步骤3: 生成优化建议
            logger.info("生成优化建议...")
            
            # 创建临时分析结果用于策略判断
            temp_result = AnalysisResult(
                database_id=database_id,
                health_score=health_score,
                wait_chains=chains,
                contentions=contentions,
                statistics=statistics,
                recommendations=[],
                timestamp=datetime.now()
            )
            
            # 生成建议
            all_advice = []
            for strategy in self.strategies:
                if strategy.is_applicable(temp_result):
                    try:
                        advice = await strategy.generate(temp_result)
                        all_advice.extend(advice)
                        logger.info(
                            f"策略 {strategy.__class__.__name__} "
                            f"生成 {len(advice)} 条建议"
                        )
                    except Exception as e:
                        logger.error(f"策略生成建议失败: {e}", exc_info=True)
            
            # 按优先级和影响分数排序
            all_advice.sort(
                key=lambda a: (
                    {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(a.priority, 3),
                    -a.impact_score
                )
            )
            
            logger.info(f"优化建议生成完成: {len(all_advice)} 条建议")
            
            # 步骤4: 构建最终结果
            result = AnalysisResult(
                database_id=database_id,
                health_score=health_score,
                wait_chains=chains,
                contentions=contentions,
                statistics=statistics,
                recommendations=all_advice,
                timestamp=datetime.now()
            )
            
            # 写入缓存
            if self.cache:
                cache_key = f"lock_analysis:{database_id}:comprehensive"
                await self.cache.set(cache_key, result, data_type='analysis')
            
            duration_sec = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"综合分析完成: 数据库 {database_id}, "
                f"耗时 {duration_sec:.2f}秒, "
                f"健康评分 {health_score:.2f}, "
                f"建议数 {len(all_advice)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"综合分析失败: {e}", exc_info=True)
            raise
    
    async def analyze_realtime(self, database_id: int) -> dict:
        """
        实时快速分析
        
        Args:
            database_id: 数据库ID
            
        Returns:
            dict: 实时分析结果
        """
        try:
            # 只采集当前锁和等待链
            locks, chains = await asyncio.gather(
                self.collector.collect_current_locks(),
                self.collector.collect_wait_chains(),
                return_exceptions=True
            )
            
            if isinstance(locks, Exception):
                locks = []
            if isinstance(chains, Exception):
                chains = []
            
            # 快速评估
            critical_chains = sum(1 for c in chains if c.severity == "critical")
            waiting_locks = sum(1 for l in locks if not l.granted)
            
            return {
                "database_id": database_id,
                "timestamp": datetime.now().isoformat(),
                "total_locks": len(locks),
                "waiting_locks": waiting_locks,
                "total_chains": len(chains),
                "critical_chains": critical_chains,
                "status": "critical" if critical_chains > 0 else "normal"
            }
            
        except Exception as e:
            logger.error(f"实时分析失败: {e}")
            return {
                "database_id": database_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "error"
            }
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 编排器是否正常工作
        """
        try:
            return await self.collector.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False