#!/usr/bin/env python3
"""
测试真正的OceanBase连接
"""

import pymysql
import time
import sys

def test_oceanbase_connection():
    """测试OceanBase连接"""
    print("🔍 测试OceanBase连接...")
    
    # 连接参数
    config = {
        'host': '127.0.0.1',
        'port': 2881,
        'user': 'root@test',
        'password': 'udbm_ob_root_password',
        'database': 'udbm_oceanbase_demo',
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    try:
        # 尝试连接
        print("📡 正在连接到OceanBase...")
        connection = pymysql.connect(**config)
        print("✅ 连接成功！")
        
        # 测试基本查询
        with connection.cursor() as cursor:
            # 查看版本信息
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"📊 OceanBase版本: {version[0]}")
            
            # 查看数据库列表
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print(f"🗄️ 数据库列表: {[db[0] for db in databases]}")
            
            # 查看当前数据库的表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"📋 表列表: {[table[0] for table in tables]}")
            
            # 测试数据查询
            if 'users' in [table[0] for table in tables]:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()
                print(f"👥 用户数量: {user_count[0]}")
                
                cursor.execute("SELECT username, full_name, role FROM users LIMIT 3")
                users = cursor.fetchall()
                print("👤 用户示例:")
                for user in users:
                    print(f"   - {user[0]} ({user[1]}) - {user[2]}")
            
            # 测试OceanBase特有的系统视图
            try:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'udbm_oceanbase_demo'")
                table_count = cursor.fetchone()
                print(f"📊 表数量: {table_count[0]}")
            except Exception as e:
                print(f"⚠️ 无法查询information_schema: {e}")
            
            # 测试性能相关查询
            try:
                cursor.execute("SHOW STATUS LIKE 'Qcache%'")
                status = cursor.fetchall()
                if status:
                    print("📈 缓存状态:")
                    for stat in status[:3]:  # 只显示前3个
                        print(f"   - {stat[0]}: {stat[1]}")
            except Exception as e:
                print(f"⚠️ 无法查询状态信息: {e}")
        
        connection.close()
        print("✅ 测试完成，连接正常！")
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def wait_for_oceanbase(max_wait=300):
    """等待OceanBase启动"""
    print(f"⏳ 等待OceanBase启动（最多等待{max_wait}秒）...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            connection = pymysql.connect(
                host='127.0.0.1',
                port=2881,
                user='root@test',
                password='udbm_ob_root_password',
                connect_timeout=5
            )
            connection.close()
            print("✅ OceanBase已启动！")
            return True
        except:
            print(".", end="", flush=True)
            time.sleep(5)
    
    print(f"\n❌ OceanBase在{max_wait}秒内未能启动")
    return False

if __name__ == "__main__":
    print("🚀 OceanBase连接测试")
    print("=" * 50)
    
    # 等待OceanBase启动
    if not wait_for_oceanbase():
        sys.exit(1)
    
    # 测试连接
    if test_oceanbase_connection():
        print("\n🎉 所有测试通过！OceanBase运行正常。")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)
