#!/usr/bin/env python3
"""
OceanBase 性能分析功能完整测试脚本
测试所有新实现的功能：GV$SQL_AUDIT分析、分区分析、API端点等
"""
import sys
import os
import requests
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'udbm-backend'))

def test_api_endpoints():
    """测试API端点"""
    print("=" * 60)
    print("测试 OceanBase API 端点")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1/performance-tuning"
    database_id = 1
    
    endpoints = [
        {
            "name": "SQL性能分析",
            "url": f"{base_url}/oceanbase/sql-analysis/{database_id}",
            "method": "GET",
            "params": {"threshold_seconds": 1.0, "hours": 24}
        },
        {
            "name": "SQL性能趋势",
            "url": f"{base_url}/oceanbase/sql-trends/{database_id}",
            "method": "GET",
            "params": {"days": 7}
        },
        {
            "name": "分区表分析",
            "url": f"{base_url}/oceanbase/partition-analysis/{database_id}",
            "method": "GET",
            "params": {}
        },
        {
            "name": "分区热点分析",
            "url": f"{base_url}/oceanbase/partition-hotspots/{database_id}",
            "method": "GET",
            "params": {}
        },
        {
            "name": "执行计划分析",
            "url": f"{base_url}/oceanbase/execution-plan",
            "method": "POST",
            "data": {"sql_text": "SELECT * FROM users WHERE user_id = 12345"}
        },
        {
            "name": "分区剪裁分析",
            "url": f"{base_url}/oceanbase/partition-pruning",
            "method": "POST",
            "data": {
                "database_id": database_id,
                "sql_queries": [
                    "SELECT * FROM orders WHERE order_date > '2025-01-01'",
                    "SELECT * FROM users WHERE user_id = 12345"
                ]
            }
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"\n测试 {endpoint['name']}...")
            
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], params=endpoint.get('params', {}))
            else:
                response = requests.post(endpoint['url'], json=endpoint.get('data', {}))
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint['name']] = {
                    "status": "success",
                    "status_code": response.status_code,
                    "data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
                    "response_size": len(str(data))
                }
                print(f"  ✅ 成功 - 状态码: {response.status_code}")
                print(f"  📊 数据字段: {len(data.keys()) if isinstance(data, dict) else 'N/A'}")
            else:
                results[endpoint['name']] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"  ❌ 失败 - 状态码: {response.status_code}")
                print(f"  📝 错误信息: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            results[endpoint['name']] = {
                "status": "connection_error",
                "error": "无法连接到API服务器"
            }
            print(f"  ❌ 连接失败 - 请确保后端服务正在运行")
        except Exception as e:
            results[endpoint['name']] = {
                "status": "exception",
                "error": str(e)
            }
            print(f"  ❌ 异常: {str(e)}")
    
    return results

def test_script_generation():
    """测试脚本生成功能"""
    print("\n" + "=" * 60)
    print("测试优化脚本生成")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1/performance-tuning"
    
    # 模拟分析结果
    mock_analysis_results = {
        "summary": {
            "total_slow_queries": 15,
            "avg_elapsed_time": 2.5,
            "slow_query_percentage": 12.5
        },
        "optimization_suggestions": [
            {
                "type": "cpu_optimization",
                "priority": "high",
                "title": "CPU密集型查询优化",
                "description": "发现5个CPU密集型查询",
                "actions": ["检查是否存在全表扫描", "优化JOIN条件和顺序"]
            }
        ],
        "index_suggestions": [
            {
                "description": "为user_id列创建索引",
                "create_index_sql": "CREATE INDEX idx_users_user_id ON users(user_id);"
            }
        ]
    }
    
    script_endpoints = [
        {
            "name": "SQL优化脚本生成",
            "url": f"{base_url}/oceanbase/generate-sql-optimization-script",
            "data": {"analysis_results": mock_analysis_results}
        },
        {
            "name": "分区优化脚本生成",
            "url": f"{base_url}/oceanbase/generate-partition-optimization-script",
            "data": {"analysis_results": mock_analysis_results}
        }
    ]
    
    results = {}
    
    for endpoint in script_endpoints:
        try:
            print(f"\n测试 {endpoint['name']}...")
            
            response = requests.post(endpoint['url'], json=endpoint['data'])
            
            if response.status_code == 200:
                data = response.json()
                script = data.get('script', '')
                results[endpoint['name']] = {
                    "status": "success",
                    "script_length": len(script),
                    "contains_recommendations": "建议" in script or "建议" in script,
                    "contains_scripts": "CREATE" in script or "ALTER" in script
                }
                print(f"  ✅ 成功 - 脚本长度: {len(script)} 字符")
                print(f"  📝 包含建议: {'建议' in script or '建议' in script}")
                print(f"  🔧 包含SQL: {'CREATE' in script or 'ALTER' in script}")
            else:
                results[endpoint['name']] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"  ❌ 失败 - 状态码: {response.status_code}")
                
        except Exception as e:
            results[endpoint['name']] = {
                "status": "exception",
                "error": str(e)
            }
            print(f"  ❌ 异常: {str(e)}")
    
    return results

def test_mock_data_quality():
    """测试Mock数据质量"""
    print("\n" + "=" * 60)
    print("测试 Mock 数据质量")
    print("=" * 60)
    
    try:
        from udbm_backend.app.services.performance_tuning.oceanbase_sql_analyzer import OceanBaseSQLAnalyzer
        from udbm_backend.app.services.performance_tuning.oceanbase_partition_analyzer import OceanBasePartitionAnalyzer
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # 创建测试数据库会话
        engine = create_engine("sqlite:///:memory:", echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # 测试SQL分析器
            sql_analyzer = OceanBaseSQLAnalyzer(db)
            
            print("\n1. 测试SQL分析器Mock数据...")
            sql_audit_records = sql_analyzer.query_sql_audit(database_id=1, limit=20)
            print(f"   📊 生成记录数: {len(sql_audit_records)}")
            
            if sql_audit_records:
                record = sql_audit_records[0]
                print(f"   ✅ 记录结构完整: {hasattr(record, 'elapsed_time')}")
                print(f"   📈 执行时间范围: {min(r.elapsed_time for r in sql_audit_records):.3f}s - {max(r.elapsed_time for r in sql_audit_records):.3f}s")
                print(f"   💾 物理读范围: {min(r.physical_reads for r in sql_audit_records)} - {max(r.physical_reads for r in sql_audit_records)}")
            
            # 测试慢查询分析
            slow_analysis = sql_analyzer.analyze_slow_queries(database_id=1)
            print(f"   🔍 慢查询分析: {slow_analysis['summary']['total_slow_queries']} 个慢查询")
            print(f"   💡 优化建议: {len(slow_analysis['optimization_suggestions'])} 条建议")
            
            # 测试分区分析器
            partition_analyzer = OceanBasePartitionAnalyzer(db)
            
            print("\n2. 测试分区分析器Mock数据...")
            partition_analysis = partition_analyzer.analyze_partition_tables(database_id=1)
            print(f"   📊 分区表数: {partition_analysis['summary']['total_partition_tables']}")
            print(f"   📈 总分区数: {partition_analysis['summary']['total_partitions']}")
            print(f"   💾 总数据量: {partition_analysis['summary']['total_size_mb']:.1f} MB")
            
            # 测试热点分析
            hotspot_analysis = partition_analyzer.analyze_partition_hotspots(database_id=1)
            print(f"   🔥 热点分区: {len(hotspot_analysis['hot_partitions'])} 个")
            print(f"   ❄️ 冷分区: {len(hotspot_analysis['cold_partitions'])} 个")
            
            print("\n✅ Mock数据质量测试完成")
            
        finally:
            db.close()
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("   请确保在udbm-backend目录中运行此脚本")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def generate_test_report(api_results, script_results):
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("测试报告汇总")
    print("=" * 60)
    
    total_tests = len(api_results) + len(script_results)
    successful_tests = sum(1 for r in api_results.values() if r['status'] == 'success')
    successful_tests += sum(1 for r in script_results.values() if r['status'] == 'success')
    
    print(f"📊 总测试数: {total_tests}")
    print(f"✅ 成功测试: {successful_tests}")
    print(f"❌ 失败测试: {total_tests - successful_tests}")
    print(f"📈 成功率: {(successful_tests / total_tests * 100):.1f}%")
    
    print("\n📋 详细结果:")
    
    print("\n🔌 API端点测试:")
    for name, result in api_results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"  {status_icon} {name}: {result['status']}")
        if result['status'] == 'success':
            print(f"     状态码: {result['status_code']}, 数据字段: {result['data_keys']}")
        elif 'error' in result:
            print(f"     错误: {result['error'][:50]}...")
    
    print("\n📝 脚本生成测试:")
    for name, result in script_results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"  {status_icon} {name}: {result['status']}")
        if result['status'] == 'success':
            print(f"     脚本长度: {result['script_length']} 字符")
            print(f"     包含建议: {result['contains_recommendations']}")
            print(f"     包含SQL: {result['contains_scripts']}")
        elif 'error' in result:
            print(f"     错误: {result['error'][:50]}...")

def main():
    """主测试函数"""
    print("🚀 OceanBase 性能分析功能完整测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 测试API端点
        api_results = test_api_endpoints()
        
        # 测试脚本生成
        script_results = test_script_generation()
        
        # 测试Mock数据质量
        test_mock_data_quality()
        
        # 生成测试报告
        generate_test_report(api_results, script_results)
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)
        
        # 提供使用建议
        print("\n💡 使用建议:")
        print("1. 确保后端服务正在运行: cd udbm-backend && python -m uvicorn app.main:app --reload")
        print("2. 访问前端页面查看OceanBase分析功能")
        print("3. 使用API端点进行集成测试")
        print("4. 查看生成的优化脚本进行实际调优")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
