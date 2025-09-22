#!/usr/bin/env python3
"""
OceanBase 性能分析功能测试脚本
测试GV$SQL_AUDIT分析、分区分析等新功能
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.performance_tuning.oceanbase_sql_analyzer import OceanBaseSQLAnalyzer
from app.services.performance_tuning.oceanbase_partition_analyzer import OceanBasePartitionAnalyzer
from app.services.db_providers.oceanbase import OceanBaseProvider


def get_test_db_session():
    """获取测试数据库会话"""
    # 创建同步引擎用于测试
    engine = create_engine("sqlite:///:memory:", echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_sql_analyzer():
    """测试SQL分析器功能"""
    print("=" * 60)
    print("测试 OceanBase SQL 分析器")
    print("=" * 60)
    
    db = get_test_db_session()
    try:
        analyzer = OceanBaseSQLAnalyzer(db)
        
        # 测试慢查询分析
        print("\n1. 测试慢查询分析...")
        slow_analysis = analyzer.analyze_slow_queries(database_id=1, threshold_seconds=1.0, hours=24)
        print(f"   慢查询总数: {slow_analysis['summary']['total_slow_queries']}")
        print(f"   平均执行时间: {slow_analysis['summary']['avg_elapsed_time']:.3f}秒")
        print(f"   优化建议数量: {len(slow_analysis['optimization_suggestions'])}")
        
        # 测试性能趋势分析
        print("\n2. 测试性能趋势分析...")
        trends = analyzer.analyze_sql_performance_trends(database_id=1, days=7)
        print(f"   分析天数: {trends['analysis_period']}")
        print(f"   每日统计数量: {len(trends['daily_stats'])}")
        print(f"   最佳SQL数量: {len(trends['top_performing_sqls'])}")
        print(f"   最差SQL数量: {len(trends['worst_performing_sqls'])}")
        
        # 测试执行计划分析
        print("\n3. 测试执行计划分析...")
        test_sql = "SELECT u.*, p.profile_data FROM users u JOIN profiles p ON u.user_id = p.user_id WHERE u.created_at > '2025-01-01'"
        plan_analysis = analyzer.analyze_sql_execution_plan(test_sql)
        print(f"   SQL: {test_sql[:50]}...")
        print(f"   预估成本: {plan_analysis['estimated_cost']}")
        print(f"   预估行数: {plan_analysis['estimated_rows']}")
        print(f"   执行计划步骤数: {len(plan_analysis['execution_plan'])}")
        print(f"   优化建议数量: {len(plan_analysis['optimization_suggestions'])}")
        
        # 测试优化脚本生成
        print("\n4. 测试优化脚本生成...")
        script = analyzer.generate_sql_optimization_script(slow_analysis)
        print(f"   脚本长度: {len(script)} 字符")
        print(f"   脚本包含索引建议: {'索引' in script}")
        print(f"   脚本包含SQL重写建议: {'SQL重写' in script}")
        
        print("\n✅ SQL分析器测试完成")
        
    except Exception as e:
        print(f"❌ SQL分析器测试失败: {str(e)}")
    finally:
        db.close()


def test_partition_analyzer():
    """测试分区分析器功能"""
    print("\n" + "=" * 60)
    print("测试 OceanBase 分区分析器")
    print("=" * 60)
    
    db = get_test_db_session()
    try:
        analyzer = OceanBasePartitionAnalyzer(db)
        
        # 测试分区表分析
        print("\n1. 测试分区表分析...")
        partition_analysis = analyzer.analyze_partition_tables(database_id=1)
        print(f"   分区表总数: {partition_analysis['summary']['total_partition_tables']}")
        print(f"   总分区数: {partition_analysis['summary']['total_partitions']}")
        print(f"   总行数: {partition_analysis['summary']['total_rows']:,}")
        print(f"   总大小: {partition_analysis['summary']['total_size_mb']:.2f} MB")
        print(f"   表分析数量: {len(partition_analysis['table_analysis'])}")
        
        # 测试热点分析
        print("\n2. 测试分区热点分析...")
        hotspot_analysis = analyzer.analyze_partition_hotspots(database_id=1)
        print(f"   热点分区数量: {len(hotspot_analysis['hot_partitions'])}")
        print(f"   冷分区数量: {len(hotspot_analysis['cold_partitions'])}")
        print(f"   热点模式数量: {len(hotspot_analysis['hotspot_patterns'])}")
        print(f"   优化建议数量: {len(hotspot_analysis['recommendations'])}")
        
        # 测试分区剪裁分析
        print("\n3. 测试分区剪裁分析...")
        test_queries = [
            "SELECT * FROM orders WHERE order_date > '2025-01-01'",
            "SELECT * FROM users WHERE user_id = 12345",
            "SELECT * FROM products WHERE category = 'electronics'",
            "SELECT * FROM logs WHERE timestamp > '2025-01-01' AND level = 'ERROR'"
        ]
        pruning_analysis = analyzer.analyze_partition_pruning(database_id=1, sql_queries=test_queries)
        print(f"   测试查询数量: {len(test_queries)}")
        print(f"   有剪裁的查询: {len(pruning_analysis['queries_with_pruning'])}")
        print(f"   无剪裁的查询: {len(pruning_analysis['queries_without_pruning'])}")
        print(f"   剪裁效率: {pruning_analysis['pruning_efficiency']:.1f}%")
        
        # 测试优化脚本生成
        print("\n4. 测试分区优化脚本生成...")
        script = analyzer.generate_partition_optimization_script(partition_analysis)
        print(f"   脚本长度: {len(script)} 字符")
        print(f"   脚本包含重构建议: {'重构建议' in script}")
        print(f"   脚本包含热点处理: {'热点分区' in script}")
        print(f"   脚本包含剪裁优化: {'剪裁优化' in script}")
        
        print("\n✅ 分区分析器测试完成")
        
    except Exception as e:
        print(f"❌ 分区分析器测试失败: {str(e)}")
    finally:
        db.close()


def test_oceanbase_provider():
    """测试OceanBase Provider集成功能"""
    print("\n" + "=" * 60)
    print("测试 OceanBase Provider 集成")
    print("=" * 60)
    
    db = get_test_db_session()
    try:
        provider = OceanBaseProvider(db)
        
        # 测试SQL分析器集成
        print("\n1. 测试SQL分析器集成...")
        sql_analysis = provider.sql_analyzer.analyze_slow_queries(database_id=1)
        print(f"   SQL分析结果: {len(sql_analysis)} 个字段")
        print(f"   包含摘要: {'summary' in sql_analysis}")
        print(f"   包含慢查询: {'top_slow_queries' in sql_analysis}")
        
        # 测试分区分析器集成
        print("\n2. 测试分区分析器集成...")
        partition_analysis = provider.partition_analyzer.analyze_partition_tables(database_id=1)
        print(f"   分区分析结果: {len(partition_analysis)} 个字段")
        print(f"   包含摘要: {'summary' in partition_analysis}")
        print(f"   包含表分析: {'table_analysis' in partition_analysis}")
        
        # 测试慢查询功能增强
        print("\n3. 测试慢查询功能增强...")
        slow_queries = provider.slow_queries.list(database_id=1, limit=10, offset=0)
        print(f"   慢查询列表: {len(slow_queries)} 条记录")
        
        patterns = provider.slow_queries.patterns(database_id=1, days=7)
        print(f"   模式分析: {len(patterns)} 个字段")
        print(f"   包含慢查询统计: {'total_slow_queries' in patterns}")
        
        statistics = provider.slow_queries.statistics(database_id=1, days=7)
        print(f"   统计信息: {len(statistics)} 个字段")
        print(f"   包含趋势: {'trend' in statistics}")
        
        # 测试执行计划分析
        print("\n4. 测试执行计划分析...")
        test_sql = "SELECT COUNT(*) FROM orders WHERE order_date BETWEEN '2025-01-01' AND '2025-12-31'"
        plan_analysis = provider.sql_analyzer.analyze_execution_plan(test_sql)
        print(f"   执行计划分析: {len(plan_analysis)} 个字段")
        print(f"   包含执行计划: {'execution_plan' in plan_analysis}")
        print(f"   包含索引使用: {'index_usage' in plan_analysis}")
        
        print("\n✅ OceanBase Provider 集成测试完成")
        
    except Exception as e:
        print(f"❌ OceanBase Provider 集成测试失败: {str(e)}")
    finally:
        db.close()


def test_mock_data_quality():
    """测试Mock数据质量"""
    print("\n" + "=" * 60)
    print("测试 Mock 数据质量")
    print("=" * 60)
    
    db = get_test_db_session()
    try:
        analyzer = OceanBaseSQLAnalyzer(db)
        
        # 测试GV$SQL_AUDIT模拟数据
        print("\n1. 测试GV$SQL_AUDIT模拟数据...")
        sql_audit_records = analyzer.query_sql_audit(database_id=1, limit=50)
        print(f"   记录数量: {len(sql_audit_records)}")
        
        if sql_audit_records:
            record = sql_audit_records[0]
            print(f"   记录字段完整性:")
            print(f"     - request_time: {hasattr(record, 'request_time')}")
            print(f"     - elapsed_time: {hasattr(record, 'elapsed_time')}")
            print(f"     - query_sql: {hasattr(record, 'query_sql')}")
            print(f"     - cpu_time: {hasattr(record, 'cpu_time')}")
            print(f"     - physical_reads: {hasattr(record, 'physical_reads')}")
            print(f"     - logical_reads: {hasattr(record, 'logical_reads')}")
            
            # 检查数据合理性
            print(f"   数据合理性检查:")
            print(f"     - 执行时间范围: {min(r.elapsed_time for r in sql_audit_records):.3f}s - {max(r.elapsed_time for r in sql_audit_records):.3f}s")
            print(f"     - CPU时间占比: {sum(r.cpu_time for r in sql_audit_records) / sum(r.elapsed_time for r in sql_audit_records) * 100:.1f}%")
            print(f"     - 物理读范围: {min(r.physical_reads for r in sql_audit_records)} - {max(r.physical_reads for r in sql_audit_records)}")
        
        # 测试分区数据质量
        print("\n2. 测试分区数据质量...")
        partition_analyzer = OceanBasePartitionAnalyzer(db)
        partition_tables = partition_analyzer._get_partition_tables(database_id=1)
        print(f"   分区表数量: {len(partition_tables)}")
        
        for table in partition_tables:
            print(f"   表 {table['table_name']}:")
            print(f"     - 分区类型: {table['partition_type'].value}")
            print(f"     - 分区数量: {table['total_partitions']}")
            print(f"     - 总行数: {table['total_rows']:,}")
            print(f"     - 总大小: {table['total_size_mb']:.2f} MB")
        
        print("\n✅ Mock 数据质量测试完成")
        
    except Exception as e:
        print(f"❌ Mock 数据质量测试失败: {str(e)}")
    finally:
        db.close()


def main():
    """主测试函数"""
    print("🚀 开始 OceanBase 性能分析功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 运行各项测试
        test_sql_analyzer()
        test_partition_analyzer()
        test_oceanbase_provider()
        test_mock_data_quality()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
