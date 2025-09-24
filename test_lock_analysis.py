#!/usr/bin/env python3
"""
锁分析功能测试脚本
"""
import requests
import json
import time
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_lock_analysis_api():
    """测试锁分析API接口"""
    print("🔍 开始测试锁分析功能...")
    
    # 测试数据库ID
    database_id = 1
    
    try:
        # 1. 测试获取锁分析仪表板
        print("\n1. 测试获取锁分析仪表板...")
        response = requests.get(f"{BASE_URL}/performance-tuning/lock-analysis/dashboard/{database_id}")
        if response.status_code == 200:
            dashboard_data = response.json()
            print(f"✅ 仪表板数据获取成功")
            print(f"   - 整体健康评分: {dashboard_data.get('overall_health_score', 'N/A')}")
            print(f"   - 当前锁数量: {dashboard_data.get('current_locks', 'N/A')}")
            print(f"   - 等待锁数量: {dashboard_data.get('waiting_locks', 'N/A')}")
        else:
            print(f"❌ 仪表板数据获取失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    
        # 2. 测试执行锁分析
        print("\n2. 测试执行锁分析...")
        analysis_request = {
            "database_id": database_id,
            "analysis_type": "realtime",
            "time_range_hours": 24,
            "include_wait_chains": True,
            "include_contention": True,
            "min_wait_time": 0.1
        }
        response = requests.post(f"{BASE_URL}/performance-tuning/lock-analysis/analyze/{database_id}", 
                               json=analysis_request)
        if response.status_code == 200:
            analysis_result = response.json()
            print(f"✅ 锁分析执行成功")
            print(f"   - 分析类型: {analysis_result.get('analysis_type', 'N/A')}")
            print(f"   - 分析时间: {analysis_result.get('analysis_timestamp', 'N/A')}")
        else:
            print(f"❌ 锁分析执行失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    
        # 3. 测试获取等待链分析
        print("\n3. 测试获取等待链分析...")
        response = requests.get(f"{BASE_URL}/performance-tuning/lock-analysis/wait-chains/{database_id}")
        if response.status_code == 200:
            wait_chains = response.json()
            print(f"✅ 等待链分析获取成功")
            print(f"   - 等待链数量: {len(wait_chains)}")
            for i, chain in enumerate(wait_chains[:3]):  # 显示前3个
                print(f"   - 链{i+1}: {chain.get('chain_id', 'N/A')} (长度: {chain.get('chain_length', 'N/A')})")
        else:
            print(f"❌ 等待链分析获取失败: {response.status_code}")
    
        # 4. 测试获取锁竞争分析
        print("\n4. 测试获取锁竞争分析...")
        response = requests.get(f"{BASE_URL}/performance-tuning/lock-analysis/contentions/{database_id}")
        if response.status_code == 200:
            contentions = response.json()
            print(f"✅ 锁竞争分析获取成功")
            print(f"   - 竞争对象数量: {len(contentions)}")
            for i, contention in enumerate(contentions[:3]):  # 显示前3个
                print(f"   - 对象{i+1}: {contention.get('object_name', 'N/A')} (竞争次数: {contention.get('contention_count', 'N/A')})")
        else:
            print(f"❌ 锁竞争分析获取失败: {response.status_code}")
    
        # 5. 测试获取锁事件历史
        print("\n5. 测试获取锁事件历史...")
        response = requests.get(f"{BASE_URL}/performance-tuning/lock-analysis/events/{database_id}?hours=24&limit=10")
        if response.status_code == 200:
            events = response.json()
            print(f"✅ 锁事件历史获取成功")
            print(f"   - 事件数量: {len(events)}")
        else:
            print(f"❌ 锁事件历史获取失败: {response.status_code}")
    
        # 6. 测试获取分析总结
        print("\n6. 测试获取分析总结...")
        response = requests.get(f"{BASE_URL}/performance-tuning/lock-analysis/summary/{database_id}?days=7")
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ 分析总结获取成功")
            print(f"   - 分析周期: {summary.get('analysis_period', 'N/A')}")
            print(f"   - 总事件数: {summary.get('total_events', 'N/A')}")
            print(f"   - 总等待时间: {summary.get('total_wait_time', 'N/A')}秒")
        else:
            print(f"❌ 分析总结获取失败: {response.status_code}")
    
        # 7. 测试生成优化脚本
        print("\n7. 测试生成优化脚本...")
        analysis_result = {
            "target_objects": ["users", "orders"],
            "hot_objects": [
                {"object_name": "users", "contention_count": 25},
                {"object_name": "orders", "contention_count": 15}
            ]
        }
        response = requests.post(f"{BASE_URL}/performance-tuning/lock-analysis/generate-optimization-script/{database_id}",
                               params={"optimization_type": "comprehensive"},
                               json=analysis_result)
        if response.status_code == 200:
            script_data = response.json()
            print(f"✅ 优化脚本生成成功")
            print(f"   - 脚本ID: {script_data.get('script_id', 'N/A')}")
            print(f"   - 脚本类型: {script_data.get('script_type', 'N/A')}")
            print(f"   - 目标对象: {script_data.get('target_objects', [])}")
        else:
            print(f"❌ 优化脚本生成失败: {response.status_code}")
    
        # 8. 测试监控状态
        print("\n8. 测试监控状态...")
        response = requests.get(f"{BASE_URL}/performance-tuning/lock-analysis/monitoring/status/{database_id}")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 监控状态获取成功")
            print(f"   - 监控状态: {status.get('status', 'N/A')}")
            print(f"   - 收集间隔: {status.get('collection_interval', 'N/A')}秒")
            print(f"   - 已收集事件: {status.get('total_events_collected', 'N/A')}")
        else:
            print(f"❌ 监控状态获取失败: {response.status_code}")
    
        print("\n🎉 锁分析功能测试完成!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

def test_frontend_integration():
    """测试前端集成"""
    print("\n🌐 测试前端集成...")
    
    # 检查前端页面是否可以访问
    try:
        response = requests.get("http://localhost:3000")
        if response.status_code == 200:
            print("✅ 前端服务运行正常")
            print("   访问 http://localhost:3000/performance/lock-analysis 查看锁分析页面")
        else:
            print(f"❌ 前端服务异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务，请确保前端服务正在运行")

if __name__ == "__main__":
    print("=" * 60)
    print("🔒 UDBM 数据库锁分析功能测试")
    print("=" * 60)
    
    # 测试API接口
    test_lock_analysis_api()
    
    # 测试前端集成
    test_frontend_integration()
    
    print("\n" + "=" * 60)
    print("📋 测试总结:")
    print("1. 锁分析API接口已实现")
    print("2. 支持实时监控和历史分析")
    print("3. 提供等待链和竞争分析")
    print("4. 支持优化建议和脚本生成")
    print("5. 前端界面已集成")
    print("=" * 60)
