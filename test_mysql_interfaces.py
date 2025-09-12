#!/usr/bin/env python3
"""
测试MySQL性能调优接口的脚本
"""

import requests
import json
import sys
import time

# API基础URL
BASE_URL = "http://localhost:8000/api/v1/performance"

# MySQL相关接口列表
MYSQL_INTERFACES = [
    "/mysql/config-analysis/1",
    "/mysql/storage-engine-analysis/1", 
    "/mysql/hardware-analysis/1",
    "/mysql/security-analysis/1",
    "/mysql/replication-analysis/1",
    "/mysql/partition-analysis/1",
    "/mysql/backup-analysis/1",
    "/mysql/optimization-summary/1",
    "/mysql/performance-insights/1"
]

MYSQL_POST_INTERFACES = [
    ("/mysql/comprehensive-analysis/1", {"include_areas": ["config", "storage"]}),
    ("/mysql/generate-tuning-script/1", {"optimization_areas": ["config"]}),
    ("/mysql/quick-optimization/1", {"focus_area": "performance"})
]

def test_interface(url, method="GET", data=None):
    """测试单个接口"""
    full_url = BASE_URL + url
    print(f"\n测试接口: {method} {full_url}")
    
    try:
        if method == "GET":
            response = requests.get(full_url, timeout=10)
        else:
            response = requests.post(full_url, json=data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ 接口调用成功")
                print(f"响应数据类型: {type(result)}")
                if isinstance(result, dict):
                    print(f"响应数据键: {list(result.keys())}")
                return True
            except json.JSONDecodeError:
                print("⚠️  响应不是有效的JSON格式")
                print(f"响应内容: {response.text[:200]}...")
                return False
        else:
            print(f"❌ 接口调用失败")
            print(f"错误信息: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试MySQL性能调优接口...")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    # 测试GET接口
    print("\n📋 测试GET接口:")
    for url in MYSQL_INTERFACES:
        total_count += 1
        if test_interface(url):
            success_count += 1
        time.sleep(0.5)  # 避免请求过于频繁
    
    # 测试POST接口
    print("\n📋 测试POST接口:")
    for url, data in MYSQL_POST_INTERFACES:
        total_count += 1
        if test_interface(url, method="POST", data=data):
            success_count += 1
        time.sleep(0.5)
    
    # 总结
    print("\n" + "=" * 60)
    print(f"📊 测试结果总结:")
    print(f"   总接口数: {total_count}")
    print(f"   成功数: {success_count}")
    print(f"   失败数: {total_count - success_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有接口测试通过!")
        return 0
    else:
        print("⚠️  部分接口测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())