#!/usr/bin/env python3
"""
数据库连接监控脚本
用于监控PostgreSQL连接数，防止连接数过多导致的问题
"""
import psycopg2
import time
import logging
import subprocess
import sys
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/isadmin/StudyCursor/UDBM/logs/db_monitor.log'),
        logging.StreamHandler()
    ]
)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'udbm_user',
    'password': 'udbm_password',
    'database': 'udbm_db'
}

# 连接数阈值
MAX_CONNECTIONS_THRESHOLD = 80  # 当连接数超过80%时发出警告
CRITICAL_CONNECTIONS_THRESHOLD = 95  # 当连接数超过95%时重启服务

def get_connection_count():
    """获取当前连接数"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM pg_stat_activity;")
        current_connections = cursor.fetchone()[0]
        cursor.execute("SHOW max_connections;")
        max_connections = int(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return current_connections, max_connections
    except Exception as e:
        logging.error(f"获取连接数失败: {e}")
        return None, None

def restart_postgres():
    """重启PostgreSQL容器"""
    try:
        logging.warning("重启PostgreSQL容器...")
        result = subprocess.run(['docker', 'restart', 'udbm-postgres'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logging.info("PostgreSQL容器重启成功")
            return True
        else:
            logging.error(f"PostgreSQL容器重启失败: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"重启PostgreSQL容器时出错: {e}")
        return False

def restart_backend():
    """重启后端服务"""
    try:
        logging.warning("重启后端服务...")
        # 杀死现有进程
        subprocess.run(['pkill', '-f', 'python.*start.py'], timeout=10)
        time.sleep(2)
        # 启动新进程
        subprocess.Popen(['python', 'start.py'], 
                        cwd='/Users/isadmin/StudyCursor/UDBM/udbm-backend')
        logging.info("后端服务重启成功")
        return True
    except Exception as e:
        logging.error(f"重启后端服务时出错: {e}")
        return False

def monitor_connections():
    """监控数据库连接"""
    while True:
        try:
            current_connections, max_connections = get_connection_count()
            
            if current_connections is None or max_connections is None:
                logging.error("无法获取连接数信息，等待30秒后重试...")
                time.sleep(30)
                continue
            
            connection_percentage = (current_connections / max_connections) * 100
            
            logging.info(f"当前连接数: {current_connections}/{max_connections} ({connection_percentage:.1f}%)")
            
            if connection_percentage >= CRITICAL_CONNECTIONS_THRESHOLD:
                logging.critical(f"连接数达到临界值 ({connection_percentage:.1f}%)，重启服务...")
                if restart_postgres():
                    time.sleep(10)  # 等待PostgreSQL重启
                    restart_backend()
                    time.sleep(30)  # 等待服务完全启动
                else:
                    logging.error("无法重启服务，请手动检查")
                    
            elif connection_percentage >= MAX_CONNECTIONS_THRESHOLD:
                logging.warning(f"连接数较高 ({connection_percentage:.1f}%)，请关注")
            
            # 每30秒检查一次
            time.sleep(30)
            
        except KeyboardInterrupt:
            logging.info("监控脚本被用户中断")
            break
        except Exception as e:
            logging.error(f"监控过程中出错: {e}")
            time.sleep(30)

if __name__ == "__main__":
    logging.info("启动数据库连接监控脚本...")
    monitor_connections()
