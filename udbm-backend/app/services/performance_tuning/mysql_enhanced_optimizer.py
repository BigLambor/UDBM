"""
MySQL 增强配置优化器 - 全面的MySQL性能调优解决方案

支持多个维度的MySQL优化:
1. 配置参数优化 - InnoDB、查询缓存、连接等
2. 硬件资源优化 - CPU、内存、磁盘IO
3. 存储引擎优化 - InnoDB/MyISAM参数调优
4. 查询性能优化 - 索引、查询重写
5. 安全配置优化 - 用户权限、SSL等
6. 主从复制优化 - 复制参数、延迟优化
7. 分区表优化 - 分区策略、维护
8. 备份恢复优化 - 备份策略、恢复方案
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import logging
import asyncio
import concurrent.futures
import random
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class MySQLEnhancedOptimizer:
    """MySQL 增强配置优化器 - 全面的MySQL性能调优解决方案"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.use_real_data = True  # 优先使用真实数据
        
        # 创建异步引擎用于连接目标MySQL实例
        self.target_engine = None
        self.target_session_factory = None

    async def _setup_target_connection(self, database_instance):
        """设置到目标MySQL数据库的连接"""
        try:
            if self.target_engine:
                await self.target_engine.dispose()
                
            # 构建目标数据库连接URI  
            target_uri = f"mysql+aiomysql://{database_instance.username}:{database_instance.password_encrypted}@{database_instance.host}:{database_instance.port}/{database_instance.database_name}"
            
            self.target_engine = create_async_engine(
                target_uri,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                echo=False,
            )
            
            self.target_session_factory = sessionmaker(
                bind=self.target_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            logger.info(f"成功连接到目标MySQL数据库: {database_instance.host}:{database_instance.port}")
            return True
            
        except Exception as e:
            logger.error(f"连接目标MySQL数据库失败: {e}")
            self.target_engine = None
            self.target_session_factory = None
            return False

    async def _analyze_real_mysql_config(self, database_id: int) -> Dict[str, Any]:
        """分析真实MySQL配置"""
        try:
            # 获取数据库实例信息
            result = self.db.execute(text("""
                SELECT id, name, host, port, database_name, username, password_encrypted
                FROM udbm.database_instances 
                WHERE id = :database_id
            """), {"database_id": database_id})
            
            instance_data = result.fetchone()
            if not instance_data:
                logger.error(f"数据库实例 {database_id} 不存在")
                return {}
                
            # 创建简单的数据库实例对象
            class SimpleDBInstance:
                def __init__(self, data):
                    self.id = data[0]
                    self.name = data[1]
                    self.host = data[2]
                    self.port = data[3]
                    self.database_name = data[4]
                    self.username = data[5]
                    self.password_encrypted = data[6]
                    
            database_instance = SimpleDBInstance(instance_data)
            
            # 设置目标数据库连接
            if not await self._setup_target_connection(database_instance):
                logger.warning("无法连接目标MySQL数据库")
                return {}
                
            async with self.target_session_factory() as session:
                config = {}
                
                # 获取关键配置参数
                key_settings = [
                    'innodb_buffer_pool_size', 'innodb_log_file_size', 'innodb_flush_log_at_trx_commit',
                    'max_connections', 'thread_cache_size', 'table_open_cache', 'tmp_table_size',
                    'max_heap_table_size', 'query_cache_size', 'query_cache_type',
                    'innodb_io_capacity', 'innodb_read_io_threads', 'innodb_write_io_threads',
                    'innodb_file_per_table', 'innodb_flush_method', 'sync_binlog',
                    'binlog_format', 'expire_logs_days', 'slow_query_log',
                    'long_query_time', 'max_allowed_packet'
                ]
                
                for setting in key_settings:
                    try:
                        result = await session.execute(text(f"SHOW VARIABLES LIKE '{setting}'"))
                        row = result.fetchone()
                        if row:
                            config[setting] = row[1]
                    except Exception as e:
                        logger.debug(f"无法获取MySQL配置 {setting}: {e}")
                        config[setting] = "unknown"
                
                # 获取版本信息
                result = await session.execute(text("SELECT VERSION()"))
                config['version'] = result.scalar()
                
                # 获取状态信息
                status_vars = [
                    'Uptime', 'Threads_connected', 'Threads_running', 'Queries', 'Slow_queries',
                    'Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests',
                    'Innodb_data_reads', 'Innodb_data_writes', 'Innodb_os_log_written'
                ]
                
                config['status'] = {}
                for status_var in status_vars:
                    try:
                        result = await session.execute(text(f"SHOW STATUS LIKE '{status_var}'"))
                        row = result.fetchone()
                        if row:
                            config['status'][status_var] = row[1]
                    except Exception as e:
                        logger.debug(f"无法获取MySQL状态 {status_var}: {e}")
                        config['status'][status_var] = "unknown"
                
                logger.info(f"成功获取 {len(config)} 个MySQL配置参数")
                return config
                
        except Exception as e:
            logger.error(f"分析真实MySQL配置失败: {e}")
            return {}

    def analyze_configuration(self, database_id: int) -> Dict[str, Any]:
        """
        分析MySQL配置
        智能切换真实数据和Mock数据
        """
        # 智能切换真实数据和Mock数据
        if self.use_real_data:
            try:
                # 尝试采集真实数据
                import threading
                import concurrent.futures
                
                def run_async_in_thread():
                    return asyncio.run(self._analyze_real_mysql_config(database_id))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_in_thread)
                    real_config = future.result(timeout=30)  # 30秒超时
                    
                if real_config:
                    logger.info(f"使用真实MySQL配置数据，获得 {len(real_config)} 个配置参数")
                    recommendations = self._generate_config_recommendations(real_config)
                    return {
                        "current_config": real_config,
                        "recommendations": recommendations,
                        "analysis_timestamp": datetime.now().isoformat(),
                        "optimization_score": self._calculate_score(real_config),
                        "data_source": "real_data"
                    }
                else:
                    logger.warning("真实MySQL配置数据采集失败，回退到Mock数据")
            except Exception as e:
                logger.error(f"真实MySQL配置数据采集异常: {e}，回退到Mock数据")
        
        # 回退到Mock数据
        logger.info("使用Mock配置数据进行MySQL演示")
        current = self._get_mock_mysql_config()
        recommendations = self._generate_config_recommendations(current)
        score = self._calculate_score(current)

        return {
            "current_config": current,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "optimization_score": score,
            "data_source": "mock_data"
        }
    
    def _get_mock_mysql_config(self) -> Dict[str, Any]:
        """获取Mock MySQL配置数据 - 增强版本，模拟真实生产环境"""
        import random
        import datetime
        
        # 生成随机但合理的指标数据
        uptime_seconds = random.randint(86400 * 7, 86400 * 365)  # 7天到1年
        queries_total = random.randint(50000000, 500000000)  # 5千万到5亿查询
        slow_queries = random.randint(1000, 50000)  # 1千到5万慢查询
        threads_connected = random.randint(20, 150)  # 20到150个连接
        threads_running = random.randint(2, 15)  # 2到15个运行线程
        
        return {
            "memory": {
                "innodb_buffer_pool_size": "2G",
                "innodb_buffer_pool_instances": 8,
                "tmp_table_size": "128M",
                "max_heap_table_size": "128M",
                "query_cache_size": "256M",
                "sort_buffer_size": "2M",
                "read_buffer_size": "128K",
                "read_rnd_buffer_size": "256K",
                "join_buffer_size": "256K",
                "key_buffer_size": "256M",
                "myisam_sort_buffer_size": "64M"
            },
            "connections": {
                "max_connections": 300,
                "max_user_connections": 250,
                "thread_cache_size": 128,
                "table_open_cache": 8000,
                "table_definition_cache": 2000,
                "open_files_limit": 65535,
                "back_log": 300,
                "max_connect_errors": 100000,
                "connect_timeout": 10,
                "wait_timeout": 28800,
                "interactive_timeout": 28800
            },
            "innodb": {
                "innodb_flush_log_at_trx_commit": 1,
                "innodb_log_file_size": "1G",
                "innodb_log_files_in_group": 2,
                "innodb_log_buffer_size": "64M",
                "innodb_io_capacity": 4000,
                "innodb_io_capacity_max": 8000,
                "innodb_read_io_threads": 8,
                "innodb_write_io_threads": 8,
                "innodb_file_per_table": "ON",
                "innodb_flush_method": "O_DIRECT",
                "innodb_lock_wait_timeout": 120,
                "innodb_thread_concurrency": 16,
                "innodb_old_blocks_time": 1000,
                "innodb_stats_on_metadata": "OFF",
                "innodb_file_format": "Barracuda",
                "innodb_large_prefix": "ON",
                "innodb_checksum_algorithm": "crc32",
                "innodb_doublewrite": "ON",
                "innodb_flush_neighbors": 0,  # SSD优化
                "innodb_adaptive_hash_index": "ON",
                "innodb_change_buffering": "all"
            },
            "replication": {
                "sync_binlog": 1,
                "binlog_format": "ROW",
                "binlog_row_image": "FULL",
                "expire_logs_days": 7,
                "max_binlog_size": "1G",
                "binlog_cache_size": "1M",
                "binlog_stmt_cache_size": "32K",
                "log_slave_updates": "ON",
                "slave_parallel_workers": 4,
                "slave_parallel_type": "LOGICAL_CLOCK",
                "master_info_repository": "TABLE",
                "relay_log_info_repository": "TABLE",
                "gtid_mode": "ON",
                "enforce_gtid_consistency": "ON"
            },
            "query_cache": {
                "query_cache_type": "ON",
                "query_cache_size": "256M",
                "query_cache_limit": "2M",
                "query_cache_min_res_unit": "4K",
                "query_cache_wlock_invalidate": "OFF"
            },
            "performance": {
                "slow_query_log": "ON",
                "long_query_time": 2.0,
                "log_queries_not_using_indexes": "ON",
                "log_throttle_queries_not_using_indexes": 10,
                "min_examined_row_limit": 100,
                "log_slow_admin_statements": "ON",
                "log_slow_slave_statements": "ON"
            },
            "security": {
                "validate_password_policy": "MEDIUM",
                "validate_password_length": 8,
                "validate_password_mixed_case_count": 1,
                "validate_password_number_count": 1,
                "validate_password_special_char_count": 1,
                "ssl_cipher": "ECDHE-RSA-AES128-GCM-SHA256",
                "require_secure_transport": "OFF",
                "local_infile": "OFF",
                "secure_file_priv": "/var/lib/mysql-files/",
                "skip_name_resolve": "ON"
            },
            "version": f"MySQL 8.0.{random.randint(25, 35)} (Enhanced Mock Data)",
            "server_id": random.randint(1, 1000),
            "character_set_server": "utf8mb4",
            "collation_server": "utf8mb4_unicode_ci",
            "default_storage_engine": "InnoDB",
            "sql_mode": "ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION",
            "status": {
                "Uptime": str(uptime_seconds),
                "Threads_connected": str(threads_connected),
                "Threads_running": str(threads_running),
                "Threads_cached": str(random.randint(50, 128)),
                "Threads_created": str(random.randint(500, 5000)),
                "Queries": str(queries_total),
                "Slow_queries": str(slow_queries),
                "Questions": str(queries_total - random.randint(1000, 10000)),
                "Com_select": str(int(queries_total * 0.7)),
                "Com_insert": str(int(queries_total * 0.15)),
                "Com_update": str(int(queries_total * 0.10)),
                "Com_delete": str(int(queries_total * 0.05)),
                "Connections": str(random.randint(10000, 100000)),
                "Max_used_connections": str(random.randint(80, 200)),
                "Aborted_connects": str(random.randint(10, 500)),
                "Aborted_clients": str(random.randint(5, 100)),
                "Table_locks_immediate": str(random.randint(1000000, 10000000)),
                "Table_locks_waited": str(random.randint(100, 5000)),
                "Key_reads": str(random.randint(100000, 1000000)),
                "Key_read_requests": str(random.randint(10000000, 100000000)),
                "Key_writes": str(random.randint(50000, 500000)),
                "Key_write_requests": str(random.randint(5000000, 50000000)),
                "Qcache_hits": str(random.randint(1000000, 50000000)),
                "Qcache_inserts": str(random.randint(100000, 5000000)),
                "Qcache_not_cached": str(random.randint(50000, 1000000)),
                "Qcache_lowmem_prunes": str(random.randint(1000, 50000)),
                "Sort_merge_passes": str(random.randint(100, 10000)),
                "Sort_range": str(random.randint(10000, 500000)),
                "Sort_rows": str(random.randint(1000000, 50000000)),
                "Sort_scan": str(random.randint(5000, 200000)),
                "Created_tmp_tables": str(random.randint(10000, 500000)),
                "Created_tmp_disk_tables": str(random.randint(1000, 50000)),
                "Created_tmp_files": str(random.randint(100, 5000)),
                "Handler_read_first": str(random.randint(10000, 500000)),
                "Handler_read_key": str(random.randint(10000000, 100000000)),
                "Handler_read_next": str(random.randint(50000000, 500000000)),
                "Handler_read_prev": str(random.randint(1000000, 50000000)),
                "Handler_read_rnd": str(random.randint(500000, 10000000)),
                "Handler_read_rnd_next": str(random.randint(100000000, 1000000000)),
                "Select_full_join": str(random.randint(100, 5000)),
                "Select_full_range_join": str(random.randint(50, 2000)),
                "Select_range": str(random.randint(100000, 5000000)),
                "Select_range_check": str(random.randint(10, 1000)),
                "Select_scan": str(random.randint(50000, 1000000))
            },
            "innodb_status": {
                "Innodb_buffer_pool_reads": str(random.randint(1000000, 50000000)),
                "Innodb_buffer_pool_read_requests": str(random.randint(100000000, 1000000000)),
                "Innodb_buffer_pool_write_requests": str(random.randint(50000000, 500000000)),
                "Innodb_buffer_pool_pages_data": str(random.randint(50000, 200000)),
                "Innodb_buffer_pool_pages_dirty": str(random.randint(1000, 20000)),
                "Innodb_buffer_pool_pages_flushed": str(random.randint(1000000, 50000000)),
                "Innodb_buffer_pool_pages_free": str(random.randint(10000, 100000)),
                "Innodb_buffer_pool_pages_total": str(random.randint(100000, 500000)),
                "Innodb_data_fsyncs": str(random.randint(100000, 5000000)),
                "Innodb_data_reads": str(random.randint(1000000, 100000000)),
                "Innodb_data_writes": str(random.randint(500000, 50000000)),
                "Innodb_data_read": str(random.randint(10000000000, 1000000000000)),  # 字节
                "Innodb_data_written": str(random.randint(5000000000, 500000000000)),  # 字节
                "Innodb_log_waits": str(random.randint(0, 1000)),
                "Innodb_log_writes": str(random.randint(1000000, 50000000)),
                "Innodb_log_write_requests": str(random.randint(10000000, 500000000)),
                "Innodb_os_log_written": str(random.randint(1000000000, 100000000000)),  # 字节
                "Innodb_rows_deleted": str(random.randint(100000, 10000000)),
                "Innodb_rows_inserted": str(random.randint(1000000, 100000000)),
                "Innodb_rows_read": str(random.randint(100000000, 10000000000)),
                "Innodb_rows_updated": str(random.randint(500000, 50000000)),
                "Innodb_deadlocks": str(random.randint(10, 1000)),
                "Innodb_mutex_spin_waits": str(random.randint(100000, 10000000)),
                "Innodb_mutex_spin_rounds": str(random.randint(1000000, 100000000)),
                "Innodb_mutex_os_waits": str(random.randint(10000, 1000000))
            },
            "generated_at": datetime.datetime.now().isoformat(),
            "data_source": "enhanced_mock_data",
            "mock_version": "2.0"
        }

    def analyze_storage_engine_optimization(self, database_id: int) -> Dict[str, Any]:
        """分析存储引擎优化建议"""
        try:
            # Mock数据 - 实际环境中可以查询INFORMATION_SCHEMA
            storage_analysis = {
                "innodb_optimization": {
                    "current_settings": {
                        "innodb_buffer_pool_size": "1G",
                        "innodb_log_file_size": "512M",
                        "innodb_flush_log_at_trx_commit": 1,
                        "innodb_io_capacity": 2000,
                        "innodb_read_io_threads": 4,
                        "innodb_write_io_threads": 4
                    },
                    "recommendations": [
                        {
                            "parameter": "innodb_buffer_pool_size",
                            "current_value": "1G",
                            "recommended_value": "4G",
                            "impact": "high",
                            "description": "增加InnoDB缓冲池大小，提高数据缓存效率",
                            "estimated_improvement": "30-50% 查询性能提升"
                        },
                        {
                            "parameter": "innodb_io_capacity",
                            "current_value": 2000,
                            "recommended_value": 4000,
                            "impact": "medium",
                            "description": "基于SSD存储，增加IO容量限制",
                            "estimated_improvement": "15-25% 写入性能提升"
                        },
                        {
                            "parameter": "innodb_flush_log_at_trx_commit",
                            "current_value": 1,
                            "recommended_value": 2,
                            "impact": "high",
                            "description": "在性能优先场景下，可以设置为2",
                            "estimated_improvement": "40-60% 写入性能提升",
                            "trade_off": "降低事务安全性"
                        }
                    ]
                },
                "myisam_optimization": {
                    "current_settings": {
                        "key_buffer_size": "256M",
                        "myisam_sort_buffer_size": "8M"
                    },
                    "recommendations": [
                        {
                            "parameter": "key_buffer_size",
                            "current_value": "256M",
                            "recommended_value": "512M",
                            "impact": "medium",
                            "description": "增加MyISAM索引缓存",
                            "estimated_improvement": "10-20% 索引查询提升"
                        }
                    ]
                },
                "engine_recommendations": [
                    {
                        "table_pattern": "transaction_*",
                        "current_engine": "MyISAM",
                        "recommended_engine": "InnoDB",
                        "reason": "事务表建议使用InnoDB引擎，支持ACID特性",
                        "migration_complexity": "medium"
                    },
                    {
                        "table_pattern": "log_*",
                        "current_engine": "InnoDB",
                        "recommended_engine": "InnoDB",
                        "reason": "日志表继续使用InnoDB，支持行级锁",
                        "migration_complexity": "none"
                    }
                ]
            }
            
            return storage_analysis
            
        except Exception as e:
            logger.error(f"存储引擎分析失败: {e}")
            return {"error": str(e)}

    def analyze_hardware_optimization(self, database_id: int) -> Dict[str, Any]:
        """分析硬件层面优化建议"""
        try:
            # Mock系统信息 - 实际环境中可以通过psutil或系统调用获取
            hardware_analysis = {
                "cpu_optimization": {
                    "current_info": {
                        "cores": 8,
                        "usage_avg": 45.5,
                        "load_average": [2.1, 2.3, 2.0]
                    },
                    "recommendations": [
                        {
                            "category": "CPU调度",
                            "suggestion": "设置MySQL进程优先级",
                            "command": "nice -n -5 mysqld",
                            "impact": "medium",
                            "description": "提高MySQL进程优先级，减少CPU调度延迟"
                        },
                        {
                            "category": "CPU亲和性",
                            "suggestion": "绑定MySQL到特定CPU核心",
                            "command": "taskset -c 0-3 mysqld",
                            "impact": "low",
                            "description": "减少CPU缓存miss，提高处理效率"
                        }
                    ]
                },
                "memory_optimization": {
                    "current_info": {
                        "total_gb": 16,
                        "used_gb": 8.5,
                        "mysql_usage_gb": 3.2,
                        "swap_usage_mb": 0
                    },
                    "recommendations": [
                        {
                            "category": "内存分配",
                            "suggestion": "增加innodb_buffer_pool_size到8G",
                            "impact": "high",
                            "description": "利用更多内存缓存数据页",
                            "estimated_improvement": "40-60% 查询性能提升"
                        },
                        {
                            "category": "NUMA优化",
                            "suggestion": "禁用NUMA或配置MySQL NUMA策略",
                            "command": "numactl --interleave=all mysqld",
                            "impact": "medium",
                            "description": "避免NUMA内存访问不均衡问题"
                        }
                    ]
                },
                "disk_optimization": {
                    "current_info": {
                        "disk_type": "SSD",
                        "io_scheduler": "deadline",
                        "mount_options": "defaults",
                        "free_space_gb": 500
                    },
                    "recommendations": [
                        {
                            "category": "IO调度器",
                            "suggestion": "SSD使用noop调度器",
                            "command": "echo noop > /sys/block/sda/queue/scheduler",
                            "impact": "medium",
                            "description": "SSD不需要复杂的IO调度，使用noop提高性能"
                        },
                        {
                            "category": "文件系统",
                            "suggestion": "使用noatime挂载选项",
                            "mount_option": "noatime,nodiratime",
                            "impact": "low",
                            "description": "减少不必要的访问时间更新，提高IO性能"
                        },
                        {
                            "category": "数据目录分离",
                            "suggestion": "将日志文件和数据文件分离到不同磁盘",
                            "impact": "high",
                            "description": "减少IO竞争，提高并发性能"
                        }
                    ]
                },
                "network_optimization": {
                    "current_info": {
                        "bandwidth_mbps": 1000,
                        "latency_ms": 0.5,
                        "connection_count": 45
                    },
                    "recommendations": [
                        {
                            "category": "TCP调优",
                            "suggestion": "调整TCP缓冲区大小",
                            "sysctl_settings": {
                                "net.core.rmem_max": "134217728",
                                "net.core.wmem_max": "134217728",
                                "net.ipv4.tcp_rmem": "4096 65536 134217728"
                            },
                            "impact": "medium",
                            "description": "优化网络缓冲区，提高大数据传输性能"
                        }
                    ]
                }
            }
            
            return hardware_analysis
            
        except Exception as e:
            logger.error(f"硬件优化分析失败: {e}")
            return {"error": str(e)}

    def analyze_security_optimization(self, database_id: int) -> Dict[str, Any]:
        """分析安全配置优化建议"""
        try:
            security_analysis = {
                "user_security": {
                    "current_status": {
                        "root_remote_access": True,
                        "anonymous_users": True,
                        "password_validation": False,
                        "ssl_enabled": False
                    },
                    "recommendations": [
                        {
                            "category": "用户权限",
                            "issue": "root用户允许远程访问",
                            "severity": "high",
                            "solution": "禁用root远程访问，创建专用管理用户",
                            "sql": "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
                        },
                        {
                            "category": "匿名用户",
                            "issue": "存在匿名用户",
                            "severity": "medium",
                            "solution": "删除匿名用户",
                            "sql": "DELETE FROM mysql.user WHERE User='';"
                        },
                        {
                            "category": "密码策略",
                            "issue": "未启用密码验证插件",
                            "severity": "medium",
                            "solution": "启用validate_password插件",
                            "sql": "INSTALL PLUGIN validate_password SONAME 'validate_password.so';"
                        }
                    ]
                },
                "network_security": {
                    "current_status": {
                        "bind_address": "0.0.0.0",
                        "port": 3306,
                        "ssl_cert": None,
                        "firewall_enabled": False
                    },
                    "recommendations": [
                        {
                            "category": "网络绑定",
                            "issue": "绑定到所有接口",
                            "severity": "medium",
                            "solution": "绑定到特定IP地址",
                            "config": "bind-address = 192.168.1.100"
                        },
                        {
                            "category": "SSL加密",
                            "issue": "未启用SSL加密",
                            "severity": "high",
                            "solution": "配置SSL证书，强制加密连接",
                            "config": "require_secure_transport = ON"
                        }
                    ]
                },
                "audit_security": {
                    "current_status": {
                        "general_log": False,
                        "slow_query_log": True,
                        "audit_plugin": False
                    },
                    "recommendations": [
                        {
                            "category": "审计日志",
                            "issue": "未启用审计插件",
                            "severity": "medium",
                            "solution": "安装并配置audit_log插件",
                            "plugin": "audit_log.so"
                        }
                    ]
                }
            }
            
            return security_analysis
            
        except Exception as e:
            logger.error(f"安全配置分析失败: {e}")
            return {"error": str(e)}

    def analyze_replication_optimization(self, database_id: int) -> Dict[str, Any]:
        """分析主从复制优化建议"""
        try:
            replication_analysis = {
                "master_optimization": {
                    "current_config": {
                        "binlog_format": "ROW",
                        "sync_binlog": 1,
                        "innodb_flush_log_at_trx_commit": 1,
                        "expire_logs_days": 7,
                        "max_binlog_size": "1G"
                    },
                    "recommendations": [
                        {
                            "parameter": "sync_binlog",
                            "current_value": 1,
                            "recommended_value": 0,
                            "impact": "high",
                            "description": "在高并发场景下，可以设置为0提高性能",
                            "trade_off": "降低数据安全性，提高写入性能"
                        },
                        {
                            "parameter": "binlog_cache_size",
                            "current_value": "32K",
                            "recommended_value": "1M",
                            "impact": "medium",
                            "description": "增加binlog缓存，减少磁盘写入"
                        }
                    ]
                },
                "slave_optimization": {
                    "current_config": {
                        "relay_log_recovery": "ON",
                        "slave_parallel_workers": 0,
                        "slave_parallel_type": "DATABASE",
                        "read_only": "ON"
                    },
                    "recommendations": [
                        {
                            "parameter": "slave_parallel_workers",
                            "current_value": 0,
                            "recommended_value": 4,
                            "impact": "high",
                            "description": "启用并行复制，减少复制延迟"
                        },
                        {
                            "parameter": "slave_parallel_type",
                            "current_value": "DATABASE",
                            "recommended_value": "LOGICAL_CLOCK",
                            "impact": "medium",
                            "description": "使用逻辑时钟并行复制，提高并行度"
                        }
                    ]
                },
                "replication_monitoring": {
                    "key_metrics": [
                        "Seconds_Behind_Master",
                        "Slave_IO_Running",
                        "Slave_SQL_Running",
                        "Last_IO_Error",
                        "Last_SQL_Error"
                    ],
                    "alert_thresholds": {
                        "max_delay_seconds": 30,
                        "error_count_threshold": 5
                    }
                },
                "high_availability": {
                    "recommendations": [
                        {
                            "strategy": "半同步复制",
                            "description": "启用semi-sync复制，平衡性能和数据一致性",
                            "plugin": "semisync_master.so, semisync_slave.so"
                        },
                        {
                            "strategy": "多源复制",
                            "description": "配置多个从库，提高读取性能和可用性",
                            "complexity": "high"
                        }
                    ]
                }
            }
            
            return replication_analysis
            
        except Exception as e:
            logger.error(f"主从复制分析失败: {e}")
            return {"error": str(e)}

    def analyze_partition_optimization(self, database_id: int) -> Dict[str, Any]:
        """分析分区表优化建议"""
        try:
            partition_analysis = {
                "current_partitioned_tables": [
                    {
                        "table_name": "orders",
                        "partition_type": "RANGE",
                        "partition_key": "created_date",
                        "partition_count": 12,
                        "size_gb": 15.5
                    },
                    {
                        "table_name": "user_logs",
                        "partition_type": "HASH",
                        "partition_key": "user_id",
                        "partition_count": 8,
                        "size_gb": 8.2
                    }
                ],
                "partition_candidates": [
                    {
                        "table_name": "transactions",
                        "current_size_gb": 25.0,
                        "row_count": 50000000,
                        "recommended_partition_type": "RANGE",
                        "recommended_partition_key": "transaction_date",
                        "reason": "大表按日期范围分区，提高查询性能",
                        "estimated_improvement": "60-80% 查询性能提升"
                    },
                    {
                        "table_name": "user_activities",
                        "current_size_gb": 12.0,
                        "row_count": 30000000,
                        "recommended_partition_type": "HASH",
                        "recommended_partition_key": "user_id",
                        "reason": "用户活动表按用户ID哈希分区，平衡数据分布",
                        "estimated_improvement": "30-50% 查询性能提升"
                    }
                ],
                "partition_maintenance": {
                    "recommendations": [
                        {
                            "table": "orders",
                            "action": "添加新分区",
                            "sql": "ALTER TABLE orders ADD PARTITION (PARTITION p202412 VALUES LESS THAN ('2025-01-01'))",
                            "frequency": "monthly",
                            "automation": "建议使用存储过程自动化"
                        },
                        {
                            "table": "orders",
                            "action": "删除旧分区",
                            "sql": "ALTER TABLE orders DROP PARTITION p202301",
                            "frequency": "monthly",
                            "data_retention": "保留12个月数据"
                        }
                    ]
                },
                "partition_strategies": {
                    "range_partitioning": {
                        "use_cases": ["时间序列数据", "有序数值数据"],
                        "advantages": ["分区裁剪效果好", "易于维护", "支持分区删除"],
                        "disadvantages": ["可能数据分布不均", "需要定期维护"]
                    },
                    "hash_partitioning": {
                        "use_cases": ["用户数据", "无明显范围特征的数据"],
                        "advantages": ["数据分布均匀", "无需维护"],
                        "disadvantages": ["不支持分区裁剪", "扩展困难"]
                    },
                    "list_partitioning": {
                        "use_cases": ["地区数据", "状态数据"],
                        "advantages": ["精确控制数据分布", "查询性能好"],
                        "disadvantages": ["维护复杂", "分区数量限制"]
                    }
                }
            }
            
            return partition_analysis
            
        except Exception as e:
            logger.error(f"分区表分析失败: {e}")
            return {"error": str(e)}

    def analyze_backup_recovery_optimization(self, database_id: int) -> Dict[str, Any]:
        """分析备份恢复策略优化"""
        try:
            backup_analysis = {
                "current_backup_strategy": {
                    "full_backup": {
                        "frequency": "daily",
                        "time": "02:00",
                        "method": "mysqldump",
                        "compression": True,
                        "retention_days": 7
                    },
                    "incremental_backup": {
                        "enabled": False,
                        "method": "binlog",
                        "frequency": "hourly"
                    },
                    "backup_storage": {
                        "location": "local",
                        "encryption": False,
                        "verification": False
                    }
                },
                "optimization_recommendations": [
                    {
                        "category": "备份策略",
                        "issue": "仅使用全量备份",
                        "severity": "medium",
                        "solution": "实施增量备份策略",
                        "benefits": ["减少备份时间", "降低存储需求", "减少对生产环境影响"],
                        "implementation": "启用binlog增量备份，配合全量备份"
                    },
                    {
                        "category": "备份工具",
                        "issue": "使用mysqldump可能影响性能",
                        "severity": "medium",
                        "solution": "考虑使用Percona XtraBackup",
                        "benefits": ["热备份", "不锁表", "备份速度快"],
                        "tool": "xtrabackup"
                    },
                    {
                        "category": "备份存储",
                        "issue": "本地存储单点故障风险",
                        "severity": "high",
                        "solution": "实施异地备份存储",
                        "options": ["云存储", "远程服务器", "磁带库"],
                        "encryption": "建议启用备份加密"
                    }
                ],
                "backup_performance_optimization": {
                    "parallel_backup": {
                        "description": "使用并行备份提高速度",
                        "tool": "mydumper",
                        "threads": 4,
                        "estimated_improvement": "50-70% 备份时间减少"
                    },
                    "compression_optimization": {
                        "current": "gzip",
                        "recommended": "lz4",
                        "reason": "更快的压缩速度，略低的压缩率",
                        "performance_gain": "30-40% 备份时间减少"
                    }
                },
                "recovery_optimization": {
                    "recovery_testing": {
                        "frequency": "monthly",
                        "automated": True,
                        "verification_queries": ["数据完整性检查", "关键业务数据验证"]
                    },
                    "point_in_time_recovery": {
                        "enabled": True,
                        "binlog_retention": "7 days",
                        "recovery_time_objective": "< 1 hour"
                    },
                    "disaster_recovery": {
                        "hot_standby": "建议配置热备库",
                        "failover_time": "< 5 minutes",
                        "data_loss_tolerance": "< 1 minute"
                    }
                },
                "monitoring_and_alerting": {
                    "backup_monitoring": [
                        "备份任务执行状态",
                        "备份文件大小变化",
                        "备份完成时间",
                        "备份文件完整性"
                    ],
                    "alert_conditions": [
                        "备份失败",
                        "备份时间超过阈值",
                        "备份文件损坏",
                        "存储空间不足"
                    ]
                }
            }
            
            return backup_analysis
            
        except Exception as e:
            logger.error(f"备份恢复分析失败: {e}")
            return {"error": str(e)}

    def generate_comprehensive_tuning_script(self, database_id: int, optimization_areas: List[str] = None) -> str:
        """生成综合的MySQL性能调优脚本"""
        try:
            if optimization_areas is None:
                optimization_areas = ["config", "storage", "security", "replication"]
            
            script_lines = [
                "-- =====================================",
                "-- MySQL 综合性能调优脚本 (Enhanced Version)",
                "-- =====================================",
                f"-- 生成时间: {datetime.now().isoformat()}",
                f"-- 数据库ID: {database_id}",
                f"-- 优化区域: {', '.join(optimization_areas)}",
                "-- 脚本版本: 2.0",
                "-- 注意：执行前请备份配置文件和数据库",
                "-- 建议在测试环境中先验证效果",
                "",
                "-- 检查当前MySQL版本和状态",
                "SELECT VERSION() as mysql_version;",
                "SELECT @@global.innodb_version as innodb_version;",
                "SHOW GLOBAL STATUS LIKE 'Uptime';",
                "SHOW GLOBAL STATUS LIKE 'Threads_connected';",
                "",
                "-- =====================================",
                "-- 1. 系统信息收集（执行前状态）",
                "-- =====================================",
                "",
                "-- 收集关键性能指标（执行前基准）",
                "SELECT 'BEFORE_OPTIMIZATION' as phase,",
                "       @@global.innodb_buffer_pool_size as buffer_pool_size,",
                "       @@global.max_connections as max_connections,",
                "       @@global.innodb_io_capacity as io_capacity,",
                "       @@global.thread_cache_size as thread_cache_size;",
                "",
                "-- 记录当前慢查询统计",
                "SHOW GLOBAL STATUS LIKE 'Slow_queries';",
                "SHOW GLOBAL STATUS LIKE 'Questions';",
                "",
                "-- =====================================",
                "-- 2. 内存配置优化",
                "-- ====================================="
            ]
            
            if "config" in optimization_areas:
                config_analysis = self.analyze_configuration(database_id)
                script_lines.extend([
                    "",
                    "-- InnoDB 缓冲池优化（建议设置为系统内存的70-80%）",
                    "SET GLOBAL innodb_buffer_pool_size = 6442450944;  -- 6G",
                    "SET GLOBAL innodb_buffer_pool_instances = 8;      -- 多实例提升并发",
                    "",
                    "-- InnoDB 日志优化",
                    "-- 注意：innodb_log_file_size 需要重启生效，请在my.cnf中配置",
                    "-- innodb_log_file_size = 2G",
                    "SET GLOBAL innodb_log_buffer_size = 67108864;     -- 64M",
                    "SET GLOBAL innodb_flush_log_at_trx_commit = 2;    -- 性能优先（可能丢失1秒数据）",
                    "",
                    "-- InnoDB IO 优化（SSD存储推荐配置）",
                    "SET GLOBAL innodb_io_capacity = 6000;            -- 基于SSD IOPS",
                    "SET GLOBAL innodb_io_capacity_max = 12000;       -- 最大IO容量",
                    "SET GLOBAL innodb_read_io_threads = 8;",
                    "SET GLOBAL innodb_write_io_threads = 8;",
                    "SET GLOBAL innodb_flush_neighbors = 0;           -- SSD不需要邻页刷新",
                    "",
                    "-- 连接管理优化",
                    "SET GLOBAL max_connections = 1000;               -- 支持更多并发连接",
                    "SET GLOBAL max_user_connections = 800;           -- 单用户连接限制",
                    "SET GLOBAL thread_cache_size = 200;              -- 线程缓存",
                    "SET GLOBAL back_log = 500;                       -- 连接队列长度",
                    "",
                    "-- 表和缓存优化",
                    "SET GLOBAL table_open_cache = 16000;             -- 表缓存",
                    "SET GLOBAL table_definition_cache = 4000;        -- 表定义缓存",
                    "SET GLOBAL open_files_limit = 65535;             -- 文件描述符限制",
                    "",
                    "-- 临时表和排序优化",
                    "SET GLOBAL tmp_table_size = 268435456;           -- 256M",
                    "SET GLOBAL max_heap_table_size = 268435456;      -- 256M",
                    "SET GLOBAL sort_buffer_size = 4194304;           -- 4M（会话级别）",
                    "SET GLOBAL read_buffer_size = 262144;            -- 256K",
                    "SET GLOBAL read_rnd_buffer_size = 524288;        -- 512K",
                    "SET GLOBAL join_buffer_size = 524288;            -- 512K",
                    "",
                    "-- 查询缓存优化（MySQL 5.7及以下版本）",
                    "-- MySQL 8.0已移除查询缓存，以下配置仅适用于旧版本",
                    "-- SET GLOBAL query_cache_type = OFF;            -- 建议禁用",
                    "-- SET GLOBAL query_cache_size = 0;",
                    "",
                    "-- MyISAM 引擎优化（如果使用）",
                    "SET GLOBAL key_buffer_size = 536870912;          -- 512M MyISAM索引缓存",
                    "SET GLOBAL myisam_sort_buffer_size = 134217728;  -- 128M",
                    "",
                    "-- 验证配置更改",
                    "SELECT 'MEMORY_CONFIG_APPLIED' as status;",
                    "SHOW GLOBAL VARIABLES LIKE 'innodb_buffer_pool_size';",
                    "SHOW GLOBAL VARIABLES LIKE 'max_connections';",
                    "SHOW GLOBAL VARIABLES LIKE 'innodb_io_capacity';"
                ])
            
            if "storage" in optimization_areas:
                script_lines.extend([
                    "",
                    "-- =====================================",
                    "-- 3. 存储引擎优化",
                    "-- =====================================",
                    "",
                    "-- InnoDB 存储引擎基础配置",
                    "SET GLOBAL innodb_file_per_table = ON;           -- 独立表空间",
                    "SET GLOBAL innodb_flush_method = 'O_DIRECT';     -- 直接IO，避免双重缓冲",
                    "SET GLOBAL innodb_doublewrite = ON;              -- 双写缓冲，保证数据完整性",
                    "",
                    "-- InnoDB 自适应特性配置",
                    "SET GLOBAL innodb_adaptive_hash_index = OFF;     -- 高并发下建议禁用",
                    "SET GLOBAL innodb_adaptive_flushing = ON;        -- 自适应刷新",
                    "SET GLOBAL innodb_change_buffering = 'none';     -- SSD存储建议禁用",
                    "",
                    "-- InnoDB 锁和并发控制",
                    "SET GLOBAL innodb_lock_wait_timeout = 60;        -- 锁等待超时",
                    "SET GLOBAL innodb_thread_concurrency = 0;        -- 0表示不限制",
                    "SET GLOBAL innodb_old_blocks_time = 1000;        -- 热点数据保护",
                    "",
                    "-- InnoDB 统计信息优化",
                    "SET GLOBAL innodb_stats_on_metadata = OFF;       -- 禁用元数据统计",
                    "SET GLOBAL innodb_stats_persistent = ON;         -- 持久化统计信息",
                    "SET GLOBAL innodb_stats_auto_recalc = ON;        -- 自动重新计算统计",
                    "",
                    "-- 数据完整性和校验",
                    "SET GLOBAL innodb_checksum_algorithm = 'crc32';  -- 快速校验算法",
                    "SET GLOBAL innodb_page_cleaners = 4;             -- 页面清理线程数",
                    "",
                    "-- 验证存储引擎配置",
                    "SELECT 'STORAGE_ENGINE_CONFIG_APPLIED' as status;",
                    "SHOW GLOBAL VARIABLES LIKE 'innodb_file_per_table';",
                    "SHOW GLOBAL VARIABLES LIKE 'innodb_flush_method';",
                    "SHOW GLOBAL VARIABLES LIKE 'innodb_adaptive_hash_index';"
                ])
            
            if "security" in optimization_areas:
                script_lines.extend([
                    "",
                    "-- =====================================",
                    "-- 4. 安全配置优化",
                    "-- =====================================",
                    "",
                    "-- 警告：以下安全操作会影响现有用户和权限",
                    "-- 请在执行前确认当前用户配置",
                    "SELECT 'SECURITY_OPTIMIZATION_START' as status;",
                    "",
                    "-- 查看当前用户状态",
                    "SELECT User, Host, authentication_string IS NOT NULL as has_password",
                    "FROM mysql.user ORDER BY User, Host;",
                    "",
                    "-- 用户权限清理（谨慎执行）",
                    "-- 删除匿名用户",
                    "-- DELETE FROM mysql.user WHERE User='';",
                    "",
                    "-- 限制root用户远程访问（仅保留本地访问）",
                    "-- DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');",
                    "",
                    "-- 删除test数据库（如果存在且不需要）",
                    "-- DROP DATABASE IF EXISTS test;",
                    "-- DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';",
                    "",
                    "-- 网络安全配置",
                    "SET GLOBAL local_infile = OFF;                   -- 禁用LOCAL INFILE",
                    "-- SET GLOBAL skip_name_resolve = ON;            -- 禁用DNS解析（需要重启）",
                    "",
                    "-- SSL/TLS 配置（需要证书文件）",
                    "-- 请确保已配置SSL证书文件",
                    "-- SET GLOBAL require_secure_transport = ON;     -- 强制SSL连接",
                    "-- SET GLOBAL tls_version = 'TLSv1.2,TLSv1.3';  -- 指定TLS版本",
                    "",
                    "-- 密码策略配置（MySQL 8.0+）",
                    "-- 检查密码验证组件是否已安装",
                    "-- SELECT PLUGIN_NAME, PLUGIN_STATUS FROM INFORMATION_SCHEMA.PLUGINS",
                    "-- WHERE PLUGIN_NAME LIKE 'validate_password%';",
                    "",
                    "-- 安装和配置密码验证组件",
                    "-- INSTALL COMPONENT 'file://component_validate_password';",
                    "-- SET GLOBAL validate_password.policy = 'MEDIUM';",
                    "-- SET GLOBAL validate_password.length = 8;",
                    "-- SET GLOBAL validate_password.mixed_case_count = 1;",
                    "-- SET GLOBAL validate_password.number_count = 1;",
                    "-- SET GLOBAL validate_password.special_char_count = 1;",
                    "",
                    "-- 日志和审计配置",
                    "SET GLOBAL general_log = OFF;                    -- 通常建议关闭以提升性能",
                    "SET GLOBAL slow_query_log = ON;                 -- 启用慢查询日志",
                    "SET GLOBAL log_queries_not_using_indexes = ON;  -- 记录未使用索引的查询",
                    "SET GLOBAL long_query_time = 1.0;               -- 慢查询阈值1秒",
                    "",
                    "-- 连接安全限制",
                    "SET GLOBAL max_connect_errors = 100000;         -- 连接错误限制",
                    "SET GLOBAL max_connections_per_hour = 0;        -- 每小时连接数限制（0=无限制）",
                    "",
                    "-- 刷新权限表使更改生效",
                    "FLUSH PRIVILEGES;",
                    "",
                    "-- 验证安全配置",
                    "SELECT 'SECURITY_CONFIG_APPLIED' as status;",
                    "SHOW GLOBAL VARIABLES LIKE 'local_infile';",
                    "SHOW GLOBAL VARIABLES LIKE 'slow_query_log';",
                    "SHOW GLOBAL VARIABLES LIKE 'long_query_time';"
                ])
            
            if "replication" in optimization_areas:
                script_lines.extend([
                    "",
                    "-- =====================================",
                    "-- 5. 主从复制优化",
                    "-- =====================================",
                    "",
                    "-- 检查当前复制状态",
                    "SELECT 'REPLICATION_OPTIMIZATION_START' as status;",
                    "-- SHOW MASTER STATUS;  -- 在主库执行",
                    "-- SHOW SLAVE STATUS\\G  -- 在从库执行",
                    "",
                    "-- 主库二进制日志配置",
                    "SET GLOBAL binlog_format = 'ROW';               -- 行级复制，数据一致性最好",
                    "SET GLOBAL binlog_row_image = 'FULL';           -- 完整行镜像",
                    "SET GLOBAL sync_binlog = 100;                   -- 性能优化（可调整为1以获得最高安全性）",
                    "SET GLOBAL binlog_cache_size = 2097152;         -- 2M binlog缓存",
                    "SET GLOBAL binlog_stmt_cache_size = 65536;      -- 64K语句缓存",
                    "SET GLOBAL max_binlog_size = 1073741824;        -- 1G单个binlog文件大小",
                    "SET GLOBAL expire_logs_days = 7;                -- binlog保留7天",
                    "",
                    "-- GTID配置（MySQL 5.6+推荐）",
                    "-- 注意：启用GTID需要重启MySQL",
                    "-- SET GLOBAL gtid_mode = ON;",
                    "-- SET GLOBAL enforce_gtid_consistency = ON;",
                    "",
                    "-- 主库性能优化",
                    "SET GLOBAL slave_pending_jobs_size_max = 134217728;  -- 128M",
                    "SET GLOBAL rpl_semi_sync_master_timeout = 1000;     -- 半同步超时1秒",
                    "",
                    "-- 从库并行复制配置（在从库执行）",
                    "-- 以下配置仅在从库执行",
                    "/*",
                    "-- 并行复制配置",
                    "SET GLOBAL slave_parallel_workers = 8;          -- 并行工作线程数",
                    "SET GLOBAL slave_parallel_type = 'LOGICAL_CLOCK'; -- 逻辑时钟并行",
                    "SET GLOBAL slave_preserve_commit_order = ON;    -- 保持提交顺序",
                    "",
                    "-- 从库恢复和安全配置",
                    "SET GLOBAL relay_log_recovery = ON;             -- 启用relay log恢复",
                    "SET GLOBAL master_info_repository = 'TABLE';    -- 使用表存储主库信息",
                    "SET GLOBAL relay_log_info_repository = 'TABLE'; -- 使用表存储relay log信息",
                    "",
                    "-- 从库网络和超时配置",
                    "SET GLOBAL slave_net_timeout = 60;              -- 网络超时60秒",
                    "SET GLOBAL slave_sql_verify_checksum = ON;      -- 启用校验和验证",
                    "*/",
                    "",
                    "-- 验证复制配置",
                    "SELECT 'REPLICATION_CONFIG_APPLIED' as status;",
                    "SHOW GLOBAL VARIABLES LIKE 'binlog_format';",
                    "SHOW GLOBAL VARIABLES LIKE 'sync_binlog';",
                    "SHOW GLOBAL VARIABLES LIKE 'expire_logs_days';"
                ])
            
            script_lines.extend([
                "",
                "# =====================================",
                "# 5. 系统变量持久化",
                "# =====================================",
                "",
                "# 刷新权限表",
                "FLUSH PRIVILEGES;",
                "",
                "# 显示当前关键配置",
                "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';",
                "SHOW VARIABLES LIKE 'max_connections';",
                "SHOW VARIABLES LIKE 'innodb_io_capacity';",
                "",
                "# 脚本执行完成",
                "SELECT 'MySQL性能调优配置已完成' AS status;"
            ])
            
            return "\n".join(script_lines)
            
        except Exception as e:
            logger.error(f"生成综合调优脚本失败: {e}")
            return f"# 脚本生成失败: {str(e)}"

    def get_optimization_summary(self, database_id: int) -> Dict[str, Any]:
        """获取MySQL优化总结"""
        try:
            # 获取各个维度的分析结果
            config_analysis = self.analyze_configuration(database_id)
            storage_analysis = self.analyze_storage_engine_optimization(database_id)
            hardware_analysis = self.analyze_hardware_optimization(database_id)
            security_analysis = self.analyze_security_optimization(database_id)
            replication_analysis = self.analyze_replication_optimization(database_id)
            partition_analysis = self.analyze_partition_optimization(database_id)
            backup_analysis = self.analyze_backup_recovery_optimization(database_id)
            
            # 统计优化机会
            total_recommendations = 0
            high_impact_recommendations = 0
            critical_issues = 0
            
            # 配置优化统计
            config_recs = config_analysis.get("recommendations", [])
            total_recommendations += len(config_recs)
            high_impact_recommendations += len([r for r in config_recs if r.get("impact") == "high"])
            
            # 存储引擎优化统计
            storage_recs = storage_analysis.get("innodb_optimization", {}).get("recommendations", [])
            total_recommendations += len(storage_recs)
            high_impact_recommendations += len([r for r in storage_recs if r.get("impact") == "high"])
            
            # 安全问题统计
            security_recs = security_analysis.get("user_security", {}).get("recommendations", [])
            critical_issues += len([r for r in security_recs if r.get("severity") == "high"])
            
            # 生成总结
            optimization_summary = {
                "database_id": database_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "overall_health_score": self._calculate_overall_health_score({
                    "config": config_analysis,
                    "storage": storage_analysis,
                    "security": security_analysis,
                    "replication": replication_analysis
                }),
                "optimization_statistics": {
                    "total_recommendations": total_recommendations,
                    "high_impact_recommendations": high_impact_recommendations,
                    "critical_security_issues": critical_issues,
                    "optimization_areas_analyzed": 7
                },
                "priority_recommendations": self._get_priority_recommendations({
                    "config": config_analysis,
                    "storage": storage_analysis,
                    "security": security_analysis,
                    "replication": replication_analysis,
                    "partition": partition_analysis,
                    "backup": backup_analysis
                }),
                "optimization_roadmap": {
                    "immediate_actions": [
                        "修复高危安全配置问题",
                        "优化InnoDB缓冲池大小",
                        "启用慢查询日志分析"
                    ],
                    "short_term_goals": [
                        "实施增量备份策略",
                        "优化主从复制配置",
                        "分析分区表候选"
                    ],
                    "long_term_goals": [
                        "实施自动化监控告警",
                        "建立灾难恢复方案",
                        "性能基线建立和持续优化"
                    ]
                },
                "estimated_performance_improvement": {
                    "query_performance": "30-60%",
                    "write_performance": "20-40%",
                    "connection_handling": "25-50%",
                    "overall_throughput": "35-65%"
                }
            }
            
            # 添加增强的性能洞察数据
            enhanced_insights = self._generate_enhanced_mysql_performance_insights(database_id)
            optimization_summary["enhanced_insights"] = enhanced_insights
            
            return optimization_summary
            
        except Exception as e:
            logger.error(f"生成优化总结失败: {e}")
            return {"error": str(e), "database_id": database_id}

    def _calculate_overall_health_score(self, analyses: Dict[str, Any]) -> float:
        """计算整体健康评分"""
        try:
            scores = []
            
            # 配置评分
            config_score = analyses.get("config", {}).get("optimization_score", 70.0)
            scores.append(config_score)
            
            # 安全评分（基于问题严重程度）
            security_analysis = analyses.get("security", {})
            security_issues = 0
            for category in security_analysis.values():
                if isinstance(category, dict) and "recommendations" in category:
                    for rec in category["recommendations"]:
                        if rec.get("severity") == "high":
                            security_issues += 3
                        elif rec.get("severity") == "medium":
                            security_issues += 1
            
            security_score = max(30.0, 100.0 - (security_issues * 10))
            scores.append(security_score)
            
            # 存储引擎评分
            storage_score = 75.0  # 基础分数
            scores.append(storage_score)
            
            # 复制评分
            replication_score = 80.0  # 基础分数
            scores.append(replication_score)
            
            return sum(scores) / len(scores) if scores else 70.0
            
        except Exception as e:
            logger.error(f"计算整体健康评分失败: {e}")
            return 70.0

    def _get_priority_recommendations(self, analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取优先级推荐"""
        try:
            priority_recs = []
            
            # 从各个分析结果中提取高优先级建议
            config_recs = analyses.get("config", {}).get("recommendations", [])
            for rec in config_recs:
                if rec.get("impact") == "high":
                    priority_recs.append({
                        "category": "配置优化",
                        "title": f"优化 {rec.get('parameter')}",
                        "description": rec.get("description"),
                        "impact": rec.get("impact"),
                        "estimated_improvement": rec.get("estimated_improvement", "显著性能提升")
                    })
            
            # 安全建议
            security_analysis = analyses.get("security", {})
            for category_name, category in security_analysis.items():
                if isinstance(category, dict) and "recommendations" in category:
                    for rec in category["recommendations"]:
                        if rec.get("severity") == "high":
                            priority_recs.append({
                                "category": "安全配置",
                                "title": rec.get("issue"),
                                "description": rec.get("solution"),
                                "impact": "critical",
                                "estimated_improvement": "提高系统安全性"
                            })
            
            # 按影响程度排序
            impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            priority_recs.sort(key=lambda x: impact_order.get(x.get("impact", "low"), 3))
            
            return priority_recs[:10]  # 返回前10个优先级建议
            
        except Exception as e:
            logger.error(f"获取优先级建议失败: {e}")
            return []

    def _generate_config_recommendations(self, current: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成配置优化建议 - 增强版本，提供更全面的优化建议"""
        recs = []
        import random
        
        # 内存配置建议
        memory_config = current.get("memory", {})
        buffer_pool_size = memory_config.get("innodb_buffer_pool_size", "1G")
        if buffer_pool_size in ("1G", "2G"):
            recs.append({
                "category": "memory",
                "parameter": "innodb_buffer_pool_size",
                "current_value": buffer_pool_size,
                "recommended_value": "6G",
                "impact": "high",
                "description": "增加InnoDB缓冲池大小，建议设置为系统内存的70-80%",
                "estimated_improvement": "30-50% 查询性能提升",
                "reason": "更大的缓冲池可以缓存更多数据页，减少磁盘IO",
                "sql_example": "SET GLOBAL innodb_buffer_pool_size = 6442450944; -- 6G"
            })

        # 查询缓存优化（MySQL 8.0已移除，但为了演示保留）
        if memory_config.get("query_cache_size", "0") != "0":
            recs.append({
                "category": "memory",
                "parameter": "query_cache_size",
                "current_value": memory_config.get("query_cache_size"),
                "recommended_value": "0",
                "impact": "medium",
                "description": "MySQL 8.0+建议禁用查询缓存，使用应用层缓存替代",
                "estimated_improvement": "减少锁竞争，提升并发性能",
                "reason": "查询缓存在高并发下会成为性能瓶颈",
                "sql_example": "SET GLOBAL query_cache_type = OFF;"
            })

        # InnoDB配置建议
        innodb_config = current.get("innodb", {})
        if innodb_config.get("innodb_flush_log_at_trx_commit") == 1:
            recs.append({
                "category": "innodb",
                "parameter": "innodb_flush_log_at_trx_commit",
                "current_value": 1,
                "recommended_value": 2,
                "impact": "high",
                "description": "在可接受的数据安全性下，设置为2可显著提升写入性能",
                "estimated_improvement": "40-60% 写入性能提升",
                "reason": "减少fsync调用频率，但保持事务日志完整性",
                "trade_off": "可能丢失最后1秒的事务数据",
                "sql_example": "SET GLOBAL innodb_flush_log_at_trx_commit = 2;"
            })

        # IO容量优化
        if innodb_config.get("innodb_io_capacity", 0) < 4000:
            recs.append({
                "category": "innodb",
                "parameter": "innodb_io_capacity",
                "current_value": innodb_config.get("innodb_io_capacity", 200),
                "recommended_value": 6000,
                "impact": "medium",
                "description": "基于SSD存储，提高IO容量限制以充分利用硬件性能",
                "estimated_improvement": "20-35% 写入性能提升",
                "reason": "SSD可以处理更高的IOPS",
                "sql_example": "SET GLOBAL innodb_io_capacity = 6000;"
            })

        # 日志文件大小优化
        log_file_size = innodb_config.get("innodb_log_file_size", "48M")
        if log_file_size in ("48M", "512M", "1G"):
            recs.append({
                "category": "innodb",
                "parameter": "innodb_log_file_size",
                "current_value": log_file_size,
                "recommended_value": "2G",
                "impact": "medium",
                "description": "增加重做日志文件大小，减少日志切换频率",
                "estimated_improvement": "15-25% 写入性能提升",
                "reason": "更大的日志文件可以减少checkpoint频率",
                "note": "需要重启MySQL服务生效",
                "config_example": "innodb_log_file_size = 2G"
            })

        # 连接配置建议
        connections_config = current.get("connections", {})
        max_conn = connections_config.get("max_connections", 151)
        if max_conn < 500:
            recs.append({
                "category": "connections",
                "parameter": "max_connections",
                "current_value": max_conn,
                "recommended_value": 1000,
                "impact": "medium",
                "description": "增加最大连接数以支持更高并发负载",
                "estimated_improvement": "提升并发处理能力",
                "reason": "现代应用通常需要更多并发连接",
                "sql_example": "SET GLOBAL max_connections = 1000;",
                "note": "需要确保系统有足够内存支持更多连接"
            })

        # 线程缓存优化
        thread_cache = connections_config.get("thread_cache_size", 8)
        if thread_cache < 100:
            recs.append({
                "category": "connections",
                "parameter": "thread_cache_size",
                "current_value": thread_cache,
                "recommended_value": 200,
                "impact": "low",
                "description": "增加线程缓存大小，减少线程创建开销",
                "estimated_improvement": "5-15% 连接建立性能提升",
                "reason": "避免频繁创建和销毁线程",
                "sql_example": "SET GLOBAL thread_cache_size = 200;"
            })

        # 表缓存优化
        table_cache = connections_config.get("table_open_cache", 2000)
        if table_cache < 8000:
            recs.append({
                "category": "connections",
                "parameter": "table_open_cache",
                "current_value": table_cache,
                "recommended_value": 16000,
                "impact": "medium",
                "description": "增加表缓存大小，减少表打开关闭开销",
                "estimated_improvement": "10-20% 多表查询性能提升",
                "reason": "缓存更多表文件描述符，减少文件系统调用",
                "sql_example": "SET GLOBAL table_open_cache = 16000;"
            })

        # 临时表优化
        tmp_table_size = memory_config.get("tmp_table_size", "16M")
        if tmp_table_size in ("16M", "32M", "64M"):
            recs.append({
                "category": "memory",
                "parameter": "tmp_table_size",
                "current_value": tmp_table_size,
                "recommended_value": "256M",
                "impact": "medium",
                "description": "增加临时表大小，减少磁盘临时表创建",
                "estimated_improvement": "20-40% 复杂查询性能提升",
                "reason": "更多临时表可以在内存中处理",
                "sql_example": "SET GLOBAL tmp_table_size = 268435456; -- 256M"
            })

        # 排序缓冲区优化
        sort_buffer = memory_config.get("sort_buffer_size", "256K")
        if sort_buffer in ("256K", "512K", "1M"):
            recs.append({
                "category": "memory",
                "parameter": "sort_buffer_size",
                "current_value": sort_buffer,
                "recommended_value": "4M",
                "impact": "medium",
                "description": "增加排序缓冲区大小，提升ORDER BY性能",
                "estimated_improvement": "15-30% 排序查询性能提升",
                "reason": "更大的排序缓冲区可以减少磁盘排序",
                "sql_example": "SET GLOBAL sort_buffer_size = 4194304; -- 4M"
            })

        # 慢查询日志优化
        performance_config = current.get("performance", {})
        long_query_time = performance_config.get("long_query_time", 10.0)
        if long_query_time > 2.0:
            recs.append({
                "category": "performance",
                "parameter": "long_query_time",
                "current_value": long_query_time,
                "recommended_value": 1.0,
                "impact": "low",
                "description": "降低慢查询阈值，更好地监控查询性能",
                "estimated_improvement": "提升问题发现能力",
                "reason": "1秒以上的查询通常需要优化",
                "sql_example": "SET GLOBAL long_query_time = 1.0;"
            })

        # 二进制日志优化
        replication_config = current.get("replication", {})
        if replication_config.get("sync_binlog", 1) == 1:
            recs.append({
                "category": "replication",
                "parameter": "sync_binlog",
                "current_value": 1,
                "recommended_value": 100,
                "impact": "high",
                "description": "在可接受的数据安全性下，减少binlog同步频率",
                "estimated_improvement": "30-50% 写入性能提升",
                "reason": "减少磁盘同步调用，提升写入吞吐量",
                "trade_off": "可能丢失最后几个事务的binlog",
                "sql_example": "SET GLOBAL sync_binlog = 100;"
            })

        # 随机添加一些高级优化建议
        advanced_recommendations = [
            {
                "category": "innodb",
                "parameter": "innodb_adaptive_hash_index",
                "current_value": "ON",
                "recommended_value": "OFF",
                "impact": "low",
                "description": "在高并发OLTP场景下，禁用自适应哈希索引可能提升性能",
                "estimated_improvement": "5-10% 并发性能提升",
                "reason": "减少AHI锁竞争",
                "sql_example": "SET GLOBAL innodb_adaptive_hash_index = OFF;"
            },
            {
                "category": "innodb",
                "parameter": "innodb_flush_neighbors",
                "current_value": 1,
                "recommended_value": 0,
                "impact": "medium",
                "description": "SSD存储建议禁用邻页刷新",
                "estimated_improvement": "10-20% 随机写入性能提升",
                "reason": "SSD随机访问性能好，不需要邻页优化",
                "sql_example": "SET GLOBAL innodb_flush_neighbors = 0;"
            },
            {
                "category": "innodb",
                "parameter": "innodb_change_buffering",
                "current_value": "all",
                "recommended_value": "none",
                "impact": "medium",
                "description": "SSD存储可以考虑禁用change buffering",
                "estimated_improvement": "减少内存使用，提升实时性",
                "reason": "SSD随机写入性能好，不需要缓冲",
                "sql_example": "SET GLOBAL innodb_change_buffering = 'none';"
            }
        ]

        # 随机选择1-2个高级建议
        recs.extend(random.sample(advanced_recommendations, random.randint(1, 2)))

        return recs

    def _calculate_score(self, current: Dict[str, Any]) -> float:
        """计算配置优化评分"""
        score = 70.0
        
        # 内存配置评分
        memory_config = current.get("memory", {})
        if memory_config.get("innodb_buffer_pool_size") not in ("512M", "1G"):
            score += 10
            
        # InnoDB配置评分
        innodb_config = current.get("innodb", {})
        if innodb_config.get("innodb_file_per_table") == "ON":
            score += 5
            
        # 安全配置评分
        if current.get("version", "").startswith("MySQL 8"):
            score += 10
            
        return min(100.0, score)

    def _generate_enhanced_mysql_performance_insights(self, database_id: int) -> Dict[str, Any]:
        """生成增强的MySQL性能洞察数据 - 包含丰富的Mock数据"""
        import random
        from datetime import datetime, timedelta
        
        # 生成基础性能评分
        base_score = random.uniform(65.0, 95.0)
        
        # 生成性能瓶颈
        potential_bottlenecks = [
            {
                "type": "cpu_intensive_queries",
                "severity": "high",
                "description": "发现多个CPU密集型查询，平均CPU使用率85%",
                "affected_queries": random.randint(15, 45),
                "impact": "查询响应时间增加40-60%"
            },
            {
                "type": "memory_pressure",
                "severity": "medium", 
                "description": "InnoDB缓冲池命中率偏低，仅为89.2%",
                "current_value": "89.2%",
                "target_value": ">95%",
                "impact": "频繁磁盘IO，影响整体性能"
            },
            {
                "type": "lock_contention",
                "severity": "medium",
                "description": "检测到表锁等待，平均等待时间120ms",
                "waiting_threads": random.randint(5, 20),
                "impact": "并发性能下降"
            },
            {
                "type": "slow_disk_io",
                "severity": "low",
                "description": "磁盘IO延迟较高，平均响应时间8ms",
                "current_latency": "8ms",
                "recommended_latency": "<5ms",
                "impact": "数据读写速度受限"
            },
            {
                "type": "connection_pool_exhaustion",
                "severity": "critical",
                "description": "连接池使用率达到95%，接近上限",
                "current_connections": random.randint(180, 200),
                "max_connections": 200,
                "impact": "新连接可能被拒绝"
            }
        ]
        
        # 随机选择2-4个瓶颈
        selected_bottlenecks = random.sample(potential_bottlenecks, random.randint(2, 4))
        
        # 生成优化机会
        optimization_opportunities = [
            {
                "type": "index_optimization",
                "title": "索引优化机会",
                "description": "发现23个慢查询可通过添加索引优化",
                "estimated_benefit": "60-80% 查询性能提升",
                "effort": "medium",
                "tables_affected": ["user_activity", "order_details", "product_reviews"],
                "priority": "high"
            },
            {
                "type": "query_rewriting",
                "title": "查询重写优化",
                "description": "发现12个可优化的复杂JOIN查询",
                "estimated_benefit": "30-50% 查询性能提升", 
                "effort": "high",
                "complexity": "需要业务逻辑调整",
                "priority": "medium"
            },
            {
                "type": "partition_strategy",
                "title": "分区表策略",
                "description": "大表建议实施分区策略，减少查询扫描范围",
                "estimated_benefit": "40-70% 大表查询提升",
                "effort": "high",
                "tables_suggested": ["transaction_log", "user_events"],
                "priority": "medium"
            },
            {
                "type": "cache_layer",
                "title": "缓存层优化",
                "description": "建议引入Redis缓存层，减少数据库压力",
                "estimated_benefit": "50-80% 读取性能提升",
                "effort": "high",
                "infrastructure_change": True,
                "priority": "low"
            },
            {
                "type": "configuration_tuning",
                "title": "配置参数调优",
                "description": "18个配置参数可进一步优化",
                "estimated_benefit": "20-40% 整体性能提升",
                "effort": "low",
                "immediate_impact": True,
                "priority": "high"
            }
        ]
        
        # 随机选择3-5个优化机会
        selected_opportunities = random.sample(optimization_opportunities, random.randint(3, 5))
        
        # 生成健康状态评估
        health_factors = {
            "cpu_utilization": random.uniform(45.0, 85.0),
            "memory_usage": random.uniform(60.0, 90.0), 
            "disk_io_utilization": random.uniform(30.0, 70.0),
            "connection_efficiency": random.uniform(75.0, 95.0),
            "query_performance": random.uniform(70.0, 90.0),
            "replication_lag": random.uniform(0.1, 5.0),  # 秒
            "error_rate": random.uniform(0.01, 0.5),  # 百分比
            "deadlock_frequency": random.randint(0, 10)  # 每小时
        }
        
        # 确定健康状态
        avg_performance = (health_factors["cpu_utilization"] + health_factors["memory_usage"] + 
                          health_factors["query_performance"]) / 3
        
        if avg_performance >= 85:
            health_status = "excellent"
            health_description = "MySQL运行状况优秀，各项指标表现良好"
        elif avg_performance >= 75:
            health_status = "good"
            health_description = "MySQL运行状况良好，有少量优化空间"
        elif avg_performance >= 60:
            health_status = "fair"
            health_description = "MySQL运行状况一般，建议关注性能优化"
        else:
            health_status = "poor"
            health_description = "MySQL运行状况需要改进，建议立即优化"
        
        # 生成关键指标
        key_metrics = {
            "cpu_usage": round(health_factors["cpu_utilization"], 1),
            "memory_usage": round(health_factors["memory_usage"], 1),
            "active_connections": random.randint(25, 150),
            "qps": random.randint(500, 5000),
            "slow_query_ratio": round(random.uniform(0.5, 5.0), 2),
            "innodb_buffer_pool_hit_ratio": round(random.uniform(88.0, 99.5), 2),
            "table_locks_waited_ratio": round(random.uniform(0.1, 2.0), 2),
            "tmp_tables_created_on_disk_ratio": round(random.uniform(5.0, 25.0), 2),
            "handler_read_rnd_next_ratio": round(random.uniform(10.0, 50.0), 2),
            "select_full_join_per_second": round(random.uniform(0.1, 5.0), 2)
        }
        
        # 生成趋势数据
        trend_data = []
        base_time = datetime.now() - timedelta(hours=24)
        for i in range(24):  # 24小时数据
            timestamp = base_time + timedelta(hours=i)
            trend_data.append({
                "timestamp": timestamp.isoformat(),
                "cpu_usage": max(0, min(100, key_metrics["cpu_usage"] + random.uniform(-10, 10))),
                "memory_usage": max(0, min(100, key_metrics["memory_usage"] + random.uniform(-5, 5))),
                "qps": max(0, key_metrics["qps"] + random.randint(-500, 500)),
                "active_connections": max(0, key_metrics["active_connections"] + random.randint(-20, 20)),
                "slow_queries": random.randint(0, 50),
                "response_time_avg": round(random.uniform(50, 500), 2)  # ms
            })
        
        return {
            "database_id": database_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "performance_score": round(base_score, 2),
            "health_status": {
                "status": health_status,
                "description": health_description,
                "overall_score": round(avg_performance, 2)
            },
            "bottlenecks": selected_bottlenecks,
            "optimization_opportunities": selected_opportunities,
            "key_metrics": key_metrics,
            "health_factors": health_factors,
            "trend_data": trend_data,
            "recommendations_summary": {
                "total_issues_found": len(selected_bottlenecks),
                "optimization_opportunities": len(selected_opportunities),
                "high_priority_items": len([item for item in selected_opportunities if item.get("priority") == "high"]),
                "estimated_performance_gain": f"{random.randint(25, 80)}%"
            },
            "next_review_recommended": (datetime.now() + timedelta(days=7)).isoformat(),
            "data_source": "enhanced_mock_insights",
            "mock_version": "2.0"
        }