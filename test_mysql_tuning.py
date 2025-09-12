#!/usr/bin/env python3
"""
MySQL 调优功能测试脚本
用于验证新增的 MySQL 性能调优功能
"""

import requests
import json
import sys
from datetime import datetime

# API 基础 URL
BASE_URL = "http://localhost:8000/api/v1/performance-tuning"

# 测试数据库 ID
DATABASE_ID = 1

def test_mysql_config_analysis():
    """测试 MySQL 配置分析"""
    print("🔍 测试 MySQL 配置分析...")
    url = f"{BASE_URL}/mysql/config-analysis/{DATABASE_ID}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 配置分析成功 - 数据源: {data.get('data_source', 'unknown')}")
            print(f"   优化评分: {data.get('optimization_score', 0):.1f}")
            print(f"   建议数量: {len(data.get('recommendations', []))}")
            return True
        else:
            print(f"❌ 配置分析失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 配置分析异常: {e}")
        return False

def test_mysql_storage_analysis():
    """测试 MySQL 存储引擎分析"""
    print("\n🔍 测试 MySQL 存储引擎分析...")
    url = f"{BASE_URL}/mysql/storage-engine-analysis/{DATABASE_ID}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            innodb_recs = len(data.get('innodb_optimization', {}).get('recommendations', []))
            engine_recs = len(data.get('engine_recommendations', []))
            print(f"✅ 存储引擎分析成功")
            print(f"   InnoDB 建议: {innodb_recs} 条")
            print(f"   引擎迁移建议: {engine_recs} 条")
            return True
        else:
            print(f"❌ 存储引擎分析失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 存储引擎分析异常: {e}")
        return False

def test_mysql_security_analysis():
    """测试 MySQL 安全分析"""
    print("\n🔍 测试 MySQL 安全分析...")
    url = f"{BASE_URL}/mysql/security-analysis/{DATABASE_ID}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            user_recs = len(data.get('user_security', {}).get('recommendations', []))
            network_recs = len(data.get('network_security', {}).get('recommendations', []))
            print(f"✅ 安全分析成功")
            print(f"   用户安全建议: {user_recs} 条")
            print(f"   网络安全建议: {network_recs} 条")
            return True
        else:
            print(f"❌ 安全分析失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 安全分析异常: {e}")
        return False

def test_mysql_comprehensive_analysis():
    """测试 MySQL 综合分析"""
    print("\n🔍 测试 MySQL 综合分析...")
    url = f"{BASE_URL}/mysql/comprehensive-analysis/{DATABASE_ID}"
    
    payload = {
        "include_areas": ["config", "storage", "security", "replication"]
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            areas = len(data.get('analysis_results', {}))
            summary = data.get('summary', {})
            health_score = summary.get('overall_health_score', 0)
            print(f"✅ 综合分析成功")
            print(f"   分析维度: {areas} 个")
            print(f"   健康评分: {health_score:.1f}")
            print(f"   总建议数: {summary.get('optimization_statistics', {}).get('total_recommendations', 0)}")
            return True
        else:
            print(f"❌ 综合分析失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 综合分析异常: {e}")
        return False

def test_mysql_tuning_script():
    """测试 MySQL 调优脚本生成"""
    print("\n🔍 测试 MySQL 调优脚本生成...")
    url = f"{BASE_URL}/mysql/generate-tuning-script/{DATABASE_ID}"
    
    params = {
        "optimization_areas": ["config", "storage"]
    }
    
    try:
        response = requests.post(url, params=params)
        if response.status_code == 200:
            data = response.json()
            script = data.get('tuning_script', '')
            script_lines = len(script.split('\n')) if script else 0
            print(f"✅ 调优脚本生成成功")
            print(f"   脚本行数: {script_lines}")
            print(f"   优化区域: {data.get('optimization_areas', [])}")
            
            # 显示脚本前几行
            if script:
                lines = script.split('\n')[:5]
                print("   脚本预览:")
                for line in lines:
                    print(f"     {line}")
                if script_lines > 5:
                    print(f"     ... (还有 {script_lines - 5} 行)")
            return True
        else:
            print(f"❌ 调优脚本生成失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 调优脚本生成异常: {e}")
        return False

def test_mysql_quick_optimization():
    """测试 MySQL 快速优化"""
    print("\n🔍 测试 MySQL 快速优化...")
    url = f"{BASE_URL}/mysql/quick-optimization/{DATABASE_ID}"
    
    params = {"focus_area": "performance"}
    
    try:
        response = requests.post(url, params=params)
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('quick_recommendations', [])
            print(f"✅ 快速优化成功")
            print(f"   重点区域: {data.get('focus_area')}")
            print(f"   快速建议: {len(recommendations)} 条")
            
            # 显示前几个建议
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec.get('category')}: {rec.get('action', '')[:50]}...")
            return True
        else:
            print(f"❌ 快速优化失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 快速优化异常: {e}")
        return False

def test_mysql_optimization_summary():
    """测试 MySQL 优化总结"""
    print("\n🔍 测试 MySQL 优化总结...")
    url = f"{BASE_URL}/mysql/optimization-summary/{DATABASE_ID}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            stats = data.get('optimization_statistics', {})
            roadmap = data.get('optimization_roadmap', {})
            print(f"✅ 优化总结成功")
            print(f"   健康评分: {data.get('overall_health_score', 0):.1f}")
            print(f"   总建议数: {stats.get('total_recommendations', 0)}")
            print(f"   高影响建议: {stats.get('high_impact_recommendations', 0)}")
            print(f"   安全问题: {stats.get('critical_security_issues', 0)}")
            print(f"   即时行动: {len(roadmap.get('immediate_actions', []))}")
            return True
        else:
            print(f"❌ 优化总结失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 优化总结异常: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 MySQL 性能调优功能测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 目标数据库ID: {DATABASE_ID}")
    print(f"🌐 API 基础URL: {BASE_URL}")
    print("=" * 60)
    
    # 执行各项测试
    tests = [
        ("MySQL 配置分析", test_mysql_config_analysis),
        ("MySQL 存储引擎分析", test_mysql_storage_analysis),
        ("MySQL 安全分析", test_mysql_security_analysis),
        ("MySQL 综合分析", test_mysql_comprehensive_analysis),
        ("MySQL 调优脚本", test_mysql_tuning_script),
        ("MySQL 快速优化", test_mysql_quick_optimization),
        ("MySQL 优化总结", test_mysql_optimization_summary),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"📈 总计: {len(results)} 个测试")
    print(f"✅ 通过: {passed} 个")
    print(f"❌ 失败: {failed} 个")
    print(f"📊 成功率: {(passed / len(results) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有测试通过！MySQL 调优功能运行正常。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查系统状态。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)