"""
锁分析模块重构 - 当前实现演示

演示已完成的功能：
1. 核心接口定义
2. 工厂模式和注册机制
3. 数据模型
4. PostgreSQL真实数据采集
"""
import asyncio
import asyncpg
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'udbm-backend'))

from app.services.lock_analysis.factories import CollectorRegistry
from app.services.lock_analysis.models import LockType, LockMode
from datetime import timedelta


async def demo_collector_registry():
    """演示采集器注册表功能"""
    print("\n" + "="*70)
    print("1. 采集器注册表演示")
    print("="*70)
    
    # 列出支持的数据库类型
    supported_types = CollectorRegistry.list_supported_types()
    print(f"\n✅ 支持的数据库类型: {supported_types}")
    
    # 获取PostgreSQL采集器类
    collector_class = CollectorRegistry.get_collector_class('postgresql')
    print(f"✅ PostgreSQL采集器类: {collector_class.__name__}")


async def demo_postgresql_collector():
    """演示PostgreSQL采集器功能"""
    print("\n" + "="*70)
    print("2. PostgreSQL采集器演示")
    print("="*70)
    
    # 注意：这里使用示例配置，实际使用时需要修改为真实的数据库配置
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    print(f"\n尝试连接到数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
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
        
        print("✅ 数据库连接池创建成功")
        
        # 创建采集器
        collector = CollectorRegistry.create_collector(
            'postgresql',
            pool=pool,
            database_id=1
        )
        
        if not collector:
            print("❌ 采集器创建失败")
            return
        
        print(f"✅ 采集器创建成功: {collector.__class__.__name__}")
        
        # 健康检查
        print("\n执行健康检查...")
        is_healthy = await collector.health_check()
        print(f"{'✅' if is_healthy else '❌'} 健康检查: {'通过' if is_healthy else '失败'}")
        
        if not is_healthy:
            print("⚠️  健康检查失败，停止演示")
            await pool.close()
            return
        
        # 采集当前锁
        print("\n采集当前锁状态...")
        locks = await collector.collect_current_locks()
        print(f"✅ 采集到 {len(locks)} 个锁")
        
        if locks:
            print("\n锁详情（前3个）:")
            for i, lock in enumerate(locks[:3], 1):
                print(f"\n  锁 #{i}:")
                print(f"    - 锁ID: {lock.lock_id}")
                print(f"    - 类型: {lock.lock_type.value}")
                print(f"    - 模式: {lock.lock_mode.value}")
                print(f"    - 对象: {lock.object_name}")
                print(f"    - 会话: {lock.session_id}")
                print(f"    - 状态: {'已授予' if lock.granted else '等待中'}")
                if lock.wait_duration:
                    print(f"    - 等待时长: {lock.wait_duration:.2f}秒")
        
        # 采集等待链
        print("\n采集锁等待链...")
        chains = await collector.collect_wait_chains()
        print(f"✅ 采集到 {len(chains)} 个等待链")
        
        if chains:
            print("\n等待链详情:")
            for i, chain in enumerate(chains, 1):
                print(f"\n  等待链 #{i}:")
                print(f"    - 链ID: {chain.chain_id}")
                print(f"    - 链长度: {chain.chain_length}")
                print(f"    - 总等待时间: {chain.total_wait_time:.2f}秒")
                print(f"    - 严重程度: {chain.severity}")
                print(f"    - 是否死锁: {'是' if chain.is_cycle else '否'}")
                if chain.get_blocking_query():
                    print(f"    - 阻塞查询: {chain.get_blocking_query()[:80]}...")
        
        # 采集统计信息
        print("\n采集锁统计信息...")
        stats = await collector.collect_statistics(timedelta(hours=1))
        print(f"✅ 统计信息采集完成")
        print(f"\n统计摘要:")
        print(f"  - 总锁数: {stats.total_locks}")
        print(f"  - 等待锁: {stats.waiting_locks}")
        print(f"  - 已授予锁: {stats.granted_locks}")
        print(f"  - 死锁次数: {stats.deadlock_count}")
        
        if stats.lock_type_distribution:
            print(f"\n  锁类型分布:")
            for lock_type, count in list(stats.lock_type_distribution.items())[:5]:
                print(f"    - {lock_type}: {count}")
        
        # 关闭连接池
        await pool.close()
        print("\n✅ 演示完成，数据库连接已关闭")
        
    except asyncpg.PostgresConnectionError as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n💡 提示:")
        print("   1. 请确保PostgreSQL正在运行")
        print("   2. 检查数据库配置信息")
        print("   3. 确认网络连接正常")
    except Exception as e:
        print(f"❌ 演示过程出错: {e}")
        import traceback
        traceback.print_exc()


async def demo_data_models():
    """演示数据模型功能"""
    print("\n" + "="*70)
    print("3. 数据模型演示")
    print("="*70)
    
    from datetime import datetime
    from app.services.lock_analysis.models import (
        LockSnapshot, WaitChain, ContentionMetrics, 
        LockStatistics, AnalysisResult, OptimizationAdvice
    )
    
    # 创建锁快照示例
    lock = LockSnapshot(
        lock_id="demo_lock_001",
        lock_type=LockType.RELATION,
        lock_mode=LockMode.ROW_EXCLUSIVE,
        database_id=1,
        object_name="users",
        session_id="12345",
        process_id=12345,
        granted=False,
        query_text="UPDATE users SET status = 'active'",
        wait_start=datetime.now()
    )
    
    print("\n✅ 锁快照示例:")
    print(f"  - 锁ID: {lock.lock_id}")
    print(f"  - 对象: {lock.object_name}")
    print(f"  - 状态: {'已授予' if lock.granted else '等待中'}")
    
    # 转换为字典
    lock_dict = lock.to_dict()
    print(f"\n✅ 转换为字典:")
    print(f"  - 字段数: {len(lock_dict)}")
    print(f"  - 包含字段: {', '.join(list(lock_dict.keys())[:5])}...")
    
    # 创建等待链示例
    chain = WaitChain(
        chain_id="demo_chain_001",
        chain_length=3,
        total_wait_time=15.5,
        head_session_id="12345",
        tail_session_id="12347",
        nodes=[
            {"pid": 12345, "query_text": "SELECT * FROM users FOR UPDATE", "level": 0},
            {"pid": 12346, "query_text": "UPDATE users SET ...", "level": 1},
            {"pid": 12347, "query_text": "DELETE FROM users WHERE ...", "level": 2}
        ],
        is_cycle=False,
        severity="high"
    )
    
    print(f"\n✅ 等待链示例:")
    print(f"  - 链长度: {chain.chain_length}")
    print(f"  - 等待时间: {chain.total_wait_time}秒")
    print(f"  - 严重程度: {chain.severity}")
    print(f"  - 阻塞查询: {chain.get_blocking_query()}")


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 锁分析模块重构 - 当前实现演示")
    print("="*70)
    print("\n本演示展示已完成的功能:")
    print("  ✅ 核心接口定义")
    print("  ✅ 工厂模式和注册机制")
    print("  ✅ 数据模型")
    print("  ✅ PostgreSQL真实数据采集")
    
    try:
        # 1. 演示采集器注册表
        await demo_collector_registry()
        
        # 2. 演示数据模型
        await demo_data_models()
        
        # 3. 演示PostgreSQL采集器（需要实际数据库）
        await demo_postgresql_collector()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("演示结束")
    print("="*70)
    print("\n📚 查看更多信息:")
    print("  - 实施进度: IMPLEMENTATION_PROGRESS.md")
    print("  - 设计方案: LOCK_ANALYSIS_REFACTORING_PROPOSAL.md")
    print("  - 代码示例: lock_analysis_refactoring_examples.py")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())