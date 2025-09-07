"""
PostgreSQL配置优化器
负责PostgreSQL数据库的配置优化和VACUUM策略
支持真实数据和Mock数据的智能切换
"""
import json
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class PostgreSQLConfigOptimizer:
    """PostgreSQL配置优化器"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.use_real_data = True  # 优先使用真实数据
        
        # 创建异步引擎用于连接目标PostgreSQL实例
        self.target_engine = None
        self.target_session_factory = None

    async def _setup_target_connection(self, database_instance):
        """设置到目标数据库的连接"""
        try:
            if self.target_engine:
                await self.target_engine.dispose()
                
            # 构建目标数据库连接URI
            target_uri = f"postgresql+asyncpg://{database_instance.username}:{database_instance.password_encrypted}@{database_instance.host}:{database_instance.port}/{database_instance.database_name}"
            
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
            
            logger.info(f"成功连接到目标数据库: {database_instance.host}:{database_instance.port}")
            return True
            
        except Exception as e:
            logger.error(f"连接目标数据库失败: {e}")
            self.target_engine = None
            self.target_session_factory = None
            return False

    async def _analyze_real_table_health(self, database_id: int) -> Dict[str, Any]:
        """分析真实PostgreSQL表健康状况"""
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
                logger.warning("无法连接目标数据库")
                return {}
                
            async with self.target_session_factory() as session:
                table_health = {
                    "critical_tables": [],
                    "warning_tables": [],
                    "healthy_tables": [],
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
                # 获取用户表的统计信息
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze,
                        vacuum_count,
                        autovacuum_count,
                        analyze_count,
                        autoanalyze_count
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """))
                
                table_stats = result.fetchall()
                
                for stat in table_stats:
                    schema_name = stat[0]
                    table_name = stat[1]
                    n_live_tup = stat[5] or 0
                    n_dead_tup = stat[6] or 0
                    last_vacuum = stat[7]
                    last_autovacuum = stat[8]
                    
                    # 计算膨胀比率
                    total_tup = n_live_tup + n_dead_tup
                    bloat_ratio = (total_tup / n_live_tup) if n_live_tup > 0 else 1.0
                    
                    # 计算自上次VACUUM以来的时间
                    last_vacuum_time = last_vacuum or last_autovacuum
                    vacuum_age_days = 0
                    if last_vacuum_time:
                        vacuum_age_days = (datetime.now() - last_vacuum_time).days
                    
                    table_info = {
                        "schema": schema_name,
                        "name": f"{schema_name}.{table_name}",
                        "live_tuples": n_live_tup,
                        "dead_tuples": n_dead_tup,
                        "bloat_ratio": bloat_ratio,
                        "last_vacuum": last_vacuum_time.isoformat() if last_vacuum_time else None,
                        "vacuum_age_days": vacuum_age_days
                    }
                    
                    # 分类表健康状况
                    if bloat_ratio > 2.0 or vacuum_age_days > 7:
                        table_health["critical_tables"].append(table_info)
                    elif bloat_ratio > 1.5 or vacuum_age_days > 3:
                        table_health["warning_tables"].append(table_info)
                    else:
                        table_health["healthy_tables"].append(table_info)
                
                logger.info(f"分析了 {len(table_stats)} 个表的健康状况")
                return table_health
                
        except Exception as e:
            logger.error(f"分析真实表健康状况失败: {e}")
            return {}

    async def _analyze_real_postgres_config(self, database_id: int) -> Dict[str, Any]:
        """分析真实PostgreSQL配置"""
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
                logger.warning("无法连接目标数据库")
                return {}
                
            async with self.target_session_factory() as session:
                config = {}
                
                # 获取关键配置参数
                key_settings = [
                    'shared_buffers', 'effective_cache_size', 'work_mem', 
                    'maintenance_work_mem', 'wal_buffers', 'max_connections',
                    'autovacuum', 'autovacuum_max_workers', 'autovacuum_naptime',
                    'checkpoint_segments', 'checkpoint_completion_target',
                    'random_page_cost', 'seq_page_cost'
                ]
                
                for setting in key_settings:
                    try:
                        result = await session.execute(text(f"SHOW {setting}"))
                        value = result.scalar()
                        config[setting] = value
                    except Exception as e:
                        logger.debug(f"无法获取配置 {setting}: {e}")
                        config[setting] = "unknown"
                
                # 获取版本信息
                result = await session.execute(text("SELECT version()"))
                config['version'] = result.scalar()
                
                logger.info(f"成功获取 {len(config)} 个配置参数")
                return config
                
        except Exception as e:
            logger.error(f"分析真实PostgreSQL配置失败: {e}")
            return {}

    def analyze_configuration(self, database_id: int) -> Dict[str, Any]:
        """
        分析PostgreSQL配置
        智能切换真实数据和Mock数据
        """
        if self.use_real_data:
            try:
                # 尝试采集真实数据
                import threading
                import concurrent.futures
                
                def run_async_in_thread():
                    return asyncio.run(self._analyze_real_postgres_config(database_id))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_in_thread)
                    real_config = future.result(timeout=30)  # 30秒超时
                    
                if real_config:
                    logger.info(f"使用真实配置数据，获得 {len(real_config)} 个配置参数")
                    recommendations = self._generate_config_recommendations(real_config)
                    return {
                        "current_config": real_config,
                        "recommendations": recommendations,
                        "analysis_timestamp": datetime.now().isoformat(),
                        "optimization_score": self._calculate_optimization_score(real_config),
                        "data_source": "real_data"
                    }
                else:
                    logger.warning("真实配置数据采集失败，回退到Mock数据")
            except Exception as e:
                logger.error(f"真实配置数据采集异常: {e}，回退到Mock数据")
        
        # 回退到Mock数据
        logger.info("使用Mock配置数据进行演示")
        current_config = self._get_current_postgres_config()
        recommendations = self._generate_config_recommendations(current_config)

        return {
            "current_config": current_config,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "optimization_score": self._calculate_optimization_score(current_config),
            "data_source": "mock_data"
        }

    def generate_vacuum_strategy(self, database_id: int) -> Dict[str, Any]:
        """
        生成VACUUM维护策略
        智能切换真实数据和Mock数据
        """
        # 分析表健康状况
        if self.use_real_data:
            try:
                # 尝试采集真实数据
                import threading
                import concurrent.futures
                
                def run_async_in_thread():
                    return asyncio.run(self._analyze_real_table_health(database_id))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_in_thread)
                    table_health = future.result(timeout=30)  # 30秒超时
                    
                if table_health:
                    logger.info(f"使用真实表健康数据，分析了 {len(table_health.get('critical_tables', [])) + len(table_health.get('warning_tables', [])) + len(table_health.get('healthy_tables', []))} 个表")
                else:
                    logger.warning("真实表健康数据采集失败，回退到Mock数据")
                    table_health = self._analyze_table_health(database_id)
            except Exception as e:
                logger.error(f"真实表健康数据采集异常: {e}，回退到Mock数据")
                table_health = self._analyze_table_health(database_id)
        else:
            table_health = self._analyze_table_health(database_id)

        # 生成VACUUM策略
        vacuum_strategy = {
            "immediate_actions": [],
            "scheduled_maintenance": [],
            "autovacuum_tuning": {},
            "monitoring_recommendations": []
        }

        # 紧急VACUUM任务
        for table in table_health["critical_tables"]:
            vacuum_strategy["immediate_actions"].append({
                "table": table["name"],
                "action": "VACUUM FULL",
                "reason": f"表膨胀严重 ({table['bloat_ratio']:.2f})",
                "estimated_duration": "30-120秒",
                "impact": "high"
            })

        # 定期维护任务
        for table in table_health["warning_tables"]:
            vacuum_strategy["scheduled_maintenance"].append({
                "table": table["name"],
                "action": "VACUUM ANALYZE",
                "frequency": "daily",
                "reason": f"表需要定期维护 ({table['bloat_ratio']:.2f})",
                "estimated_duration": "10-60秒"
            })

        # AutoVacuum配置建议
        vacuum_strategy["autovacuum_tuning"] = {
            "autovacuum_max_workers": 6,
            "autovacuum_naptime": "10s",
            "autovacuum_vacuum_threshold": 50,
            "autovacuum_analyze_threshold": 50,
            "autovacuum_vacuum_scale_factor": 0.02,
            "autovacuum_analyze_scale_factor": 0.01
        }

        return vacuum_strategy

    def optimize_memory_settings(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化PostgreSQL内存设置
        """
        total_memory_gb = system_info.get("total_memory_gb", 8)

        # 基于系统内存计算推荐配置
        recommendations = {
            "shared_buffers": f"{int(total_memory_gb * 0.25 * 1024)}MB",  # 25% of RAM
            "effective_cache_size": f"{int(total_memory_gb * 0.75 * 1024)}MB",  # 75% of RAM
            "work_mem": "4MB",  # 基础值，根据查询复杂度调整
            "maintenance_work_mem": f"{int(total_memory_gb * 0.05 * 1024)}MB",  # 5% of RAM
            "wal_buffers": "16MB",
            "temp_buffers": "8MB"
        }

        return {
            "current_memory": f"{total_memory_gb}GB",
            "recommendations": recommendations,
            "optimization_rationale": {
                "shared_buffers": "用于缓存数据页，建议设为系统内存的25%",
                "effective_cache_size": "告诉查询规划器可用的OS缓存大小",
                "work_mem": "单个操作可用的内存，影响排序和哈希操作",
                "maintenance_work_mem": "VACUUM、CREATE INDEX等维护操作使用的内存"
            }
        }

    def optimize_connection_settings(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化PostgreSQL连接设置
        """
        max_connections = workload_info.get("max_connections", 100)
        active_connections = workload_info.get("active_connections", 20)

        recommendations = {
            "max_connections": min(max_connections, 200),  # 限制最大连接数
            "shared_preload_libraries": "pg_stat_statements,auto_explain",
            "track_activity_query_size": "4096",
            "track_counts": "on",
            "track_functions": "all"
        }

        # 连接池建议
        if active_connections > max_connections * 0.7:
            recommendations["pool_suggestions"] = {
                "use_connection_pooler": True,
                "recommended_pool_size": int(max_connections * 0.8),
                "pool_mode": "transaction"
            }

        return {
            "current_connections": active_connections,
            "max_connections": max_connections,
            "recommendations": recommendations,
            "connection_pooling": recommendations.get("pool_suggestions")
        }

    def generate_performance_tuning_script(self, analysis_results: Dict[str, Any]) -> str:
        """
        生成性能调优脚本
        """
        script_lines = [
            "# PostgreSQL Performance Tuning Script",
            f"# Generated at: {datetime.now().isoformat()}",
            "",
            "# Memory Settings"
        ]

        # 内存设置
        if "memory_optimization" in analysis_results:
            mem_opt = analysis_results["memory_optimization"]
            for param, value in mem_opt["recommendations"].items():
                script_lines.append(f"ALTER SYSTEM SET {param} = '{value}';")

        script_lines.extend([
            "",
            "# Connection Settings"
        ])

        # 连接设置
        if "connection_optimization" in analysis_results:
            conn_opt = analysis_results["connection_optimization"]
            for param, value in conn_opt["recommendations"].items():
                if isinstance(value, str):
                    script_lines.append(f"ALTER SYSTEM SET {param} = '{value}';")
                elif isinstance(value, bool):
                    script_lines.append(f"ALTER SYSTEM SET {param} = {'on' if value else 'off'};")

        script_lines.extend([
            "",
            "# Maintenance Settings"
        ])

        # 维护设置
        vacuum_strategy = analysis_results.get("vacuum_strategy", {})
        if "autovacuum_tuning" in vacuum_strategy:
            for param, value in vacuum_strategy["autovacuum_tuning"].items():
                if isinstance(value, str):
                    script_lines.append(f"ALTER SYSTEM SET {param} = '{value}';")
                else:
                    script_lines.append(f"ALTER SYSTEM SET {param} = {value};")

        script_lines.extend([
            "",
            "# Reload configuration",
            "SELECT pg_reload_conf();",
            "",
            "# Show current settings",
            "SELECT name, setting, unit FROM pg_settings WHERE name IN (",
            "    'shared_buffers', 'work_mem', 'maintenance_work_mem',",
            "    'effective_cache_size', 'autovacuum_max_workers'",
            ") ORDER BY name;"
        ])

        return "\n".join(script_lines)

    def _get_current_postgres_config(self) -> Dict[str, Any]:
        """
        获取当前PostgreSQL配置（模拟）
        """
        return {
            "memory": {
                "shared_buffers": "128MB",
                "work_mem": "1MB",
                "maintenance_work_mem": "16MB",
                "effective_cache_size": "512MB"
            },
            "connections": {
                "max_connections": 100,
                "shared_preload_libraries": "",
                "track_counts": "on"
            },
            "maintenance": {
                "autovacuum_max_workers": 3,
                "autovacuum_vacuum_threshold": 50,
                "autovacuum_analyze_threshold": 50
            },
            "wal": {
                "wal_buffers": "4MB",
                "checkpoint_segments": 3,
                "wal_level": "minimal"
            }
        }

    def _generate_config_recommendations(self, current_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成配置优化建议
        """
        recommendations = []

        # 内存配置建议
        memory_config = current_config.get("memory", {})
        if memory_config.get("shared_buffers") == "128MB":
            recommendations.append({
                "category": "memory",
                "parameter": "shared_buffers",
                "current_value": "128MB",
                "recommended_value": "512MB-1GB",
                "impact": "high",
                "description": "shared_buffers太小，建议增加到系统内存的25%",
                "rationale": "PostgreSQL用于缓存数据页的主要内存区域"
            })

        if memory_config.get("work_mem") == "1MB":
            recommendations.append({
                "category": "memory",
                "parameter": "work_mem",
                "current_value": "1MB",
                "recommended_value": "4MB-16MB",
                "impact": "medium",
                "description": "work_mem太小，可能导致过多临时文件",
                "rationale": "单个操作可用的内存，影响排序和哈希操作"
            })

        # 连接配置建议
        connection_config = current_config.get("connections", {})
        if not connection_config.get("shared_preload_libraries"):
            recommendations.append({
                "category": "monitoring",
                "parameter": "shared_preload_libraries",
                "current_value": "",
                "recommended_value": "pg_stat_statements,auto_explain",
                "impact": "medium",
                "description": "建议加载监控扩展",
                "rationale": "提供查询统计和自动EXPLAIN功能"
            })

        # WAL配置建议
        wal_config = current_config.get("wal", {})
        if wal_config.get("wal_level") == "minimal":
            recommendations.append({
                "category": "wal",
                "parameter": "wal_level",
                "current_value": "minimal",
                "recommended_value": "replica",
                "impact": "low",
                "description": "建议启用WAL归档以支持复制",
                "rationale": "minimal级别不支持流复制和点-in-time恢复"
            })

        return recommendations

    def _calculate_optimization_score(self, config: Dict[str, Any]) -> float:
        """
        计算配置优化评分
        """
        score = 50.0  # 基础分数

        # 内存配置评分
        memory_config = config.get("memory", {})
        if memory_config.get("shared_buffers") not in ["128MB", "256MB"]:
            score += 20
        if memory_config.get("work_mem") not in ["1MB", "2MB"]:
            score += 10

        # 监控配置评分
        connection_config = config.get("connections", {})
        if connection_config.get("shared_preload_libraries"):
            score += 15

        return min(100.0, score)

    def _analyze_table_health(self, database_id: int) -> Dict[str, Any]:
        """
        分析表健康状况
        """
        # Mock 表健康数据
        return {
            "critical_tables": [
                {"name": "large_table_1", "bloat_ratio": 3.2, "dead_tuples": 50000},
                {"name": "large_table_2", "bloat_ratio": 2.8, "dead_tuples": 30000}
            ],
            "warning_tables": [
                {"name": "medium_table_1", "bloat_ratio": 1.8, "dead_tuples": 10000},
                {"name": "medium_table_2", "bloat_ratio": 1.6, "dead_tuples": 8000}
            ],
            "healthy_tables": [
                {"name": "small_table_1", "bloat_ratio": 1.1, "dead_tuples": 100},
                {"name": "small_table_2", "bloat_ratio": 1.0, "dead_tuples": 50}
            ],
            "total_tables": 50,
            "tables_needing_vacuum": 12,
            "avg_bloat_ratio": 1.45
        }
