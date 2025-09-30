"""
锁分析模块 - 完整功能演示

演示重构后的完整功能：
1. 数据采集（PostgreSQL + MySQL）
2. 智能分析（等待链 + 竞争 + 健康评分）
3. 优化建议（索引 + 查询优化）
4. 缓存管理
5. 分析编排
"""
import asyncio
import asyncpg
import sys
import os
from datetime import timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'udbm-backend'))

from app.services.lock_analysis import (
    LockAnalysisOrchestrator,
    LockAnalysisCache,
    CollectorRegistry,
    AnalyzerRegistry,
    StrategyRegistry
)


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


async def demo_collectors():
    """演示数据采集器"""
    print_section("1. 数据采集器演示")
    
    # 列出支持的数据库类型
    supported_types = CollectorRegistry.list_supported_types()
    print(f"✅ 支持的数据库类型: {', '.join(supported_types)}")
    
    # 显示各采集器的特点
    print("\n📊 采集器功能:")
    print("  • PostgreSQL:")
    print("    - 从 pg_locks 和 pg_stat_activity 采集实时锁信息")
    print("    - 使用递归CTE检测完整的等待链和死锁环路")
    print("    - 采集死锁统计和锁类型分布")
    
    print("\n  • MySQL:")
    print("    - 支持 MySQL 5.7 和 8.0+")
    print("    - 自动检测版本并选择合适的查询语句")
    print("    - 从 performance_schema 和 information_schema 采集锁信息")
    print("    - 分析 InnoDB 锁和锁等待")


async def demo_analyzers():
    """演示分析器"""
    print_section("2. 分析引擎演示")
    
    # 列出所有分析器
    analyzers = AnalyzerRegistry.list_analyzers()
    print(f"✅ 注册的分析器: {', '.join(analyzers)}")
    
    print("\n🔍 分析器功能:")
    print("  • WaitChainAnalyzer (等待链分析器):")
    print("    - 分析锁等待链的长度和等待时间")
    print("    - 识别死锁和长时间阻塞")
    print("    - 按严重程度分级 (critical, high, medium, low)")
    print("    - 生成针对性解决建议")
    
    print("\n  • ContentionAnalyzer (竞争分析器):")
    print("    - 识别热点对象和竞争模式")
    print("    - 模式类型: hot_spot, burst, frequent, timeout_prone")
    print("    - 统计竞争次数、等待时间、影响会话数")
    print("    - 按总等待时间排序")
    
    print("\n  • LockHealthScorer (健康评分器):")
    print("    - 多维度加权评分模型 (0-100分)")
    print("    - 等待时间 (30%), 竞争程度 (25%), 死锁 (20%)")
    print("    - 阻塞链 (15%), 超时 (10%)")
    print("    - 综合评估系统锁性能健康状况")


async def demo_strategies():
    """演示优化策略"""
    print_section("3. 优化建议生成器演示")
    
    # 列出所有策略
    strategies = StrategyRegistry.list_strategies()
    print(f"✅ 注册的优化策略: {', '.join(strategies)}")
    
    print("\n💡 优化策略功能:")
    print("  • IndexOptimizationStrategy (索引优化策略):")
    print("    - 识别热点表和频繁竞争对象")
    print("    - 生成详细的索引创建SQL脚本")
    print("    - 提供回滚方案和影响评估")
    print("    - 包含索引分析和监控指南")
    
    print("\n  • QueryOptimizationStrategy (查询优化策略):")
    print("    - 识别长时间运行和阻塞的查询")
    print("    - 生成查询优化指南和执行计划分析")
    print("    - 提供事务优化建议")
    print("    - 系统级性能优化建议")


async def demo_cache():
    """演示缓存管理"""
    print_section("4. 缓存管理演示")
    
    print("✅ 多级缓存架构:")
    print("  • L1: 本地内存缓存")
    print("    - TTL: 60秒")
    print("    - 容量: 1000条目")
    print("    - 使用LRU驱逐策略")
    print("    - 响应时间: <1ms")
    
    print("\n  • L2: Redis分布式缓存")
    print("    - 实时数据: 10秒TTL")
    print("    - 分析结果: 5分钟TTL")
    print("    - 历史数据: 1小时TTL")
    print("    - 统计数据: 30分钟TTL")
    
    print("\n💾 缓存策略:")
    print("  1. 查询时先检查本地缓存")
    print("  2. 本地缓存未命中则查询Redis")
    print("  3. Redis未命中则执行实际查询")
    print("  4. 结果写入Redis和本地缓存")
    print("  5. 支持模式匹配批量失效")


async def demo_complete_analysis():
    """演示完整的分析流程"""
    print_section("5. 完整分析流程演示")
    
    print("🔄 分析流程:")
    print("  步骤1: 并发采集数据")
    print("    → collect_current_locks()")
    print("    → collect_wait_chains()")
    print("    → collect_statistics()")
    
    print("\n  步骤2: 执行分析")
    print("    → ContentionAnalyzer.analyze(locks)")
    print("    → WaitChainAnalyzer.analyze(chains)")
    print("    → LockHealthScorer.analyze(chains, contentions, statistics)")
    
    print("\n  步骤3: 生成优化建议")
    print("    → IndexOptimizationStrategy.generate()")
    print("    → QueryOptimizationStrategy.generate()")
    
    print("\n  步骤4: 结果聚合")
    print("    → 按优先级和影响分数排序")
    print("    → 返回完整的AnalysisResult")
    
    print("\n  步骤5: 缓存写入")
    print("    → 写入Redis缓存")
    print("    → 写入本地缓存")


async def demo_real_analysis():
    """演示真实的分析（需要数据库连接）"""
    print_section("6. 真实分析演示")
    
    print("💻 连接PostgreSQL数据库...")
    
    # 数据库配置（修改为实际配置）
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    try:
        # 创建连接池
        pool = await asyncpg.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            min_size=2,
            max_size=5,
            timeout=10
        )
        
        print(f"✅ 连接成功: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # 创建采集器
        collector = CollectorRegistry.create_collector(
            'postgresql',
            pool=pool,
            database_id=1
        )
        
        # 创建缓存（不使用Redis，只用本地缓存）
        cache = LockAnalysisCache(
            enable_local=True,
            enable_redis=False
        )
        
        # 创建编排器
        orchestrator = LockAnalysisOrchestrator(
            collector=collector,
            cache=cache
        )
        
        print("\n🔍 执行综合分析...")
        
        # 执行分析
        result = await orchestrator.analyze_comprehensive(
            database_id=1,
            duration=timedelta(hours=1)
        )
        
        # 显示结果
        print(f"\n📊 分析结果:")
        print(f"  健康评分: {result.health_score:.2f}/100")
        
        # 健康状态
        if result.health_score >= 90:
            status = "优秀 ✨"
        elif result.health_score >= 70:
            status = "良好 ✓"
        elif result.health_score >= 50:
            status = "一般 ⚠️"
        else:
            status = "较差 ❌"
        print(f"  健康状态: {status}")
        
        print(f"\n  锁统计:")
        print(f"    - 总锁数: {result.statistics.total_locks}")
        print(f"    - 等待锁: {result.statistics.waiting_locks}")
        print(f"    - 已授予锁: {result.statistics.granted_locks}")
        print(f"    - 死锁次数: {result.statistics.deadlock_count}")
        
        print(f"\n  分析详情:")
        print(f"    - 等待链数量: {len(result.wait_chains)}")
        if result.wait_chains:
            critical = sum(1 for c in result.wait_chains if c.severity == "critical")
            high = sum(1 for c in result.wait_chains if c.severity == "high")
            print(f"      • 严重: {critical}, 高优先级: {high}")
        
        print(f"    - 竞争对象数: {len(result.contentions)}")
        if result.contentions:
            hot_spots = sum(1 for c in result.contentions if c.pattern == "hot_spot")
            print(f"      • 热点竞争: {hot_spots}")
        
        print(f"\n  优化建议: {len(result.recommendations)} 条")
        
        # 显示前3条建议
        for i, advice in enumerate(result.recommendations[:3], 1):
            print(f"\n  建议 #{i}:")
            print(f"    [{advice.priority.upper()}] {advice.title}")
            print(f"    类型: {advice.type}")
            print(f"    影响分数: {advice.impact_score:.1f}/100")
            print(f"    预期改善: {advice.estimated_improvement}")
            print(f"    操作步骤: {len(advice.actions)} 步")
        
        if len(result.recommendations) > 3:
            print(f"\n  ... 还有 {len(result.recommendations) - 3} 条建议")
        
        # 关闭连接池
        await pool.close()
        print("\n✅ 分析完成，连接已关闭")
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        print("\n💡 提示:")
        print("  1. 确保PostgreSQL正在运行")
        print("  2. 检查数据库配置信息")
        print("  3. 确认网络连接正常")
        print("  4. 可以修改上面的 db_config 为实际配置")


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 锁分析模块 - 完整功能演示")
    print("="*80)
    
    print("\n本演示展示重构后的所有核心功能:")
    print("  ✅ 真实数据采集 (PostgreSQL + MySQL)")
    print("  ✅ 智能分析引擎 (等待链 + 竞争 + 健康评分)")
    print("  ✅ 优化建议生成 (索引 + 查询优化)")
    print("  ✅ 多级缓存管理 (本地 + Redis)")
    print("  ✅ 分析流程编排 (异步并发)")
    
    try:
        # 1. 演示采集器
        await demo_collectors()
        
        # 2. 演示分析器
        await demo_analyzers()
        
        # 3. 演示优化策略
        await demo_strategies()
        
        # 4. 演示缓存管理
        await demo_cache()
        
        # 5. 演示完整流程
        await demo_complete_analysis()
        
        # 6. 演示真实分析（可选）
        print("\n" + "="*80)
        choice = input("\n是否执行真实数据库分析? (需要PostgreSQL连接) [y/N]: ")
        if choice.lower() == 'y':
            await demo_real_analysis()
        else:
            print("\n⏭️  跳过真实分析演示")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("演示结束")
    print("="*80)
    
    print("\n📚 查看更多信息:")
    print("  • 实施完成报告: IMPLEMENTATION_COMPLETE.md")
    print("  • 实施进度: IMPLEMENTATION_PROGRESS.md")
    print("  • 设计方案: LOCK_ANALYSIS_REFACTORING_PROPOSAL.md")
    print("  • 快速指南: LOCK_ANALYSIS_REFACTORING_QUICK_GUIDE.md")
    print("  • 架构图: LOCK_ANALYSIS_ARCHITECTURE_DIAGRAM.md")
    
    print("\n💻 代码位置:")
    print("  /workspace/udbm-backend/app/services/lock_analysis/")
    
    print("\n🎉 重构核心功能已完成！从MVP到生产就绪！")


if __name__ == "__main__":
    asyncio.run(main())