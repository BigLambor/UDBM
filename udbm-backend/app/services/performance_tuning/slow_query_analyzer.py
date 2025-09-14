"""
慢查询分析器
负责捕获、分析和优化慢查询
支持真实数据和Mock数据的智能切换
"""
import hashlib
import json
import logging
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.performance_tuning import SlowQuery, IndexSuggestion
from app.models.database import DatabaseInstance
from app.core.config import settings

logger = logging.getLogger(__name__)


class SlowQueryAnalyzer:
    """慢查询分析器"""

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

    async def _capture_real_slow_queries(self, database_id: int, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """捕获真实PostgreSQL慢查询"""
        try:
            # 获取数据库实例信息
            from sqlalchemy import text
            result = self.db.execute(text("""
                SELECT id, name, host, port, database_name, username, password_encrypted
                FROM udbm.database_instances 
                WHERE id = :database_id
            """), {"database_id": database_id})
            
            instance_data = result.fetchone()
            if not instance_data:
                logger.error(f"数据库实例 {database_id} 不存在")
                return []
                
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
                logger.warning("无法连接目标数据库，将使用Mock数据")
                return []
                
            slow_queries = []
                
            # 1. 从pg_stat_statements获取慢查询
            async with self.target_session_factory() as fresh_session:
                try:
                    # 先检查pg_stat_statements是否可用
                    result = await fresh_session.execute(text("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                        )
                    """))
                    
                    if result.scalar():
                        # 获取慢查询统计信息
                        result = await fresh_session.execute(text("""
                            SELECT 
                                query,
                                calls,
                                total_exec_time,
                                mean_exec_time,
                                rows,
                                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                            FROM pg_stat_statements 
                            WHERE mean_exec_time > :threshold * 1000  -- 转换为毫秒
                            ORDER BY mean_exec_time DESC 
                            LIMIT 50
                        """), {"threshold": threshold_seconds})
                        
                        pg_stat_queries = result.fetchall()
                        
                        for query_stat in pg_stat_queries:
                            query_text = query_stat[0]
                            calls = query_stat[1]
                            total_time = query_stat[2] / 1000.0  # 转换为秒
                            mean_time = query_stat[3] / 1000.0   # 转换为秒
                            rows_returned = query_stat[4]
                            hit_percent = query_stat[5] or 0
                            
                            # 生成查询哈希
                            query_hash = hashlib.md5(query_text.encode()).hexdigest()
                            
                            slow_queries.append({
                                "database_id": database_id,
                                "query_text": query_text,
                                "query_hash": query_hash,
                                "execution_time": mean_time,
                                "lock_time": 0.0,  # pg_stat_statements不提供锁时间
                                "rows_sent": rows_returned,
                                "rows_examined": int(rows_returned * (100 - hit_percent) / 100) if hit_percent else rows_returned,
                                "user_host": "pg_stat_statements",
                                "sql_command": self._extract_sql_command(query_text),
                                "timestamp": datetime.now(),
                                "status": "active",
                                "source": "real_data"
                            })
                    else:
                        logger.info("pg_stat_statements扩展未安装，跳过统计信息采集")
                        
                except Exception as e:
                    logger.warning(f"无法从pg_stat_statements获取数据: {e}")
                
            # 2. 从当前活跃查询中获取慢查询（使用新会话）
            async with self.target_session_factory() as fresh_session:
                try:
                    result = await fresh_session.execute(text(f"""
                        SELECT 
                            pid,
                            now() - query_start as duration,
                            query,
                            state,
                            client_addr,
                            application_name
                        FROM pg_stat_activity 
                        WHERE state = 'active' 
                        AND query_start IS NOT NULL
                        AND now() - query_start > interval '{threshold_seconds} seconds'
                        AND query NOT LIKE '%pg_stat_activity%'
                        ORDER BY duration DESC
                        LIMIT 20
                    """))
                    
                    active_queries = result.fetchall()
                    
                    for active_query in active_queries:
                        pid = active_query[0]
                        duration = active_query[1]
                        query_text = active_query[2]
                        state = active_query[3]
                        client_addr = active_query[4]
                        app_name = active_query[5]
                        
                        if query_text and duration:
                            duration_seconds = duration.total_seconds()
                            query_hash = hashlib.md5(query_text.encode()).hexdigest()
                            
                            slow_queries.append({
                                "database_id": database_id,
                                "query_text": query_text,
                                "query_hash": query_hash,
                                "execution_time": duration_seconds,
                                "lock_time": 0.0,
                                "rows_sent": 0,  # 活跃查询未完成，无法知道返回行数
                                "rows_examined": 0,
                                "user_host": f"{app_name}@{client_addr}" if client_addr else app_name or "unknown",
                                "sql_command": self._extract_sql_command(query_text),
                                "timestamp": datetime.now(),
                                "status": "active",
                                "source": "real_data"
                            })
                            
                except Exception as e:
                    logger.warning(f"无法从pg_stat_activity获取数据: {e}")
                
            # 3. 从日志中获取慢查询（如果启用了log_min_duration_statement）
            async with self.target_session_factory() as fresh_session:
                try:
                    # 检查是否启用了慢查询日志
                    result = await fresh_session.execute(text("SHOW log_min_duration_statement"))
                    log_setting = result.scalar()
                    
                    if log_setting and log_setting != '-1':
                        logger.info(f"慢查询日志已启用，阈值: {log_setting}ms")
                        # 注意：从日志文件读取需要文件系统访问权限，这里暂时跳过
                        # 实际生产环境中可以通过日志收集系统获取
                        
                except Exception as e:
                    logger.debug(f"检查慢查询日志配置失败: {e}")
                
                logger.info(f"成功采集 {len(slow_queries)} 个真实慢查询")
                return slow_queries
                
        except Exception as e:
            logger.error(f"采集真实慢查询失败: {e}")
            return []

    def _extract_sql_command(self, query_text: str) -> str:
        """提取SQL命令类型"""
        if not query_text:
            return "UNKNOWN"
            
        query_upper = query_text.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return "SELECT"
        elif query_upper.startswith('INSERT'):
            return "INSERT"
        elif query_upper.startswith('UPDATE'):
            return "UPDATE"
        elif query_upper.startswith('DELETE'):
            return "DELETE"
        elif query_upper.startswith('CREATE'):
            return "CREATE"
        elif query_upper.startswith('ALTER'):
            return "ALTER"
        elif query_upper.startswith('DROP'):
            return "DROP"
        else:
            return "OTHER"

    def capture_slow_queries(self, database_id: int, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """
        捕获慢查询
        智能切换真实数据和Mock数据
        """
        if self.use_real_data:
            try:
                # 尝试采集真实数据
                import threading
                import concurrent.futures
                
                def run_async_in_thread():
                    return asyncio.run(self._capture_real_slow_queries(database_id, threshold_seconds))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_in_thread)
                    real_queries = future.result(timeout=30)  # 30秒超时
                    
                if real_queries:
                    logger.info(f"使用真实数据采集，获得 {len(real_queries)} 个慢查询")
                    return real_queries
                else:
                    logger.warning("真实数据采集失败或无慢查询，回退到Mock数据")
            except Exception as e:
                logger.error(f"真实数据采集异常: {e}，回退到Mock数据")
        
        # 回退到Mock数据
        logger.info("使用Mock数据进行演示")
        return self._capture_mock_slow_queries(database_id, threshold_seconds)

    def _capture_mock_slow_queries(self, database_id: int, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """
        采集Mock演示慢查询 - 保持原有的丰富Mock数据逻辑
        """
        import hashlib
        from datetime import datetime, timedelta
        import random

        # 使用数据库ID作为种子的一部分，确保数据的一致性
        seed = int(hashlib.md5(f"slow_queries_{database_id}_{datetime.now().hour}".encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)

        mock_slow_queries = [
            # 复杂JOIN查询 - 最常见的慢查询类型
            {
                "query_text": "SELECT u.name, u.email, p.title, p.created_at, c.name as category_name FROM users u LEFT JOIN posts p ON u.id = p.user_id LEFT JOIN categories c ON p.category_id = c.id WHERE u.created_at >= '2023-01-01' AND u.status = 'active' AND p.published = true ORDER BY p.created_at DESC LIMIT 100",
                "execution_time": 4.2 + random.uniform(-1, 1),
                "rows_examined": 250000 + random.randint(-50000, 50000),
                "rows_sent": 100,
                "user_host": "web_app_01",
                "sql_command": "SELECT"
            },
            # 没有索引的范围查询
            {
                "query_text": "SELECT * FROM orders WHERE created_at BETWEEN '2023-06-01' AND '2023-06-30' AND total_amount > 500 AND status IN ('pending', 'processing') ORDER BY created_at",
                "execution_time": 3.8 + random.uniform(-0.8, 0.8),
                "rows_examined": 180000 + random.randint(-30000, 30000),
                "rows_sent": 5000,
                "user_host": "reporting_service",
                "sql_command": "SELECT"
            },
            # 子查询导致的性能问题
            {
                "query_text": "UPDATE products SET last_updated = NOW() WHERE category_id IN (SELECT id FROM categories WHERE parent_id IN (SELECT id FROM category_groups WHERE active = true)) AND stock_quantity < 10",
                "execution_time": 2.9 + random.uniform(-0.5, 0.5),
                "rows_examined": 120000 + random.randint(-20000, 20000),
                "rows_sent": 0,
                "user_host": "inventory_system",
                "sql_command": "UPDATE"
            },
            # 聚合查询没有合适索引
            {
                "query_text": "SELECT DATE(created_at), COUNT(*), SUM(total_amount), AVG(total_amount) FROM orders WHERE created_at >= '2023-01-01' GROUP BY DATE(created_at) ORDER BY DATE(created_at) DESC",
                "execution_time": 5.1 + random.uniform(-1.2, 1.2),
                "rows_examined": 350000 + random.randint(-70000, 70000),
                "rows_sent": 365,
                "user_host": "analytics_dashboard",
                "sql_command": "SELECT"
            },
            # LIKE查询导致全表扫描
            {
                "query_text": "SELECT * FROM products WHERE LOWER(name) LIKE '%laptop%' OR LOWER(description) LIKE '%computer%' AND price BETWEEN 500 AND 2000 ORDER BY price ASC",
                "execution_time": 6.5 + random.uniform(-1.5, 1.5),
                "rows_examined": 500000 + random.randint(-100000, 100000),
                "rows_sent": 250,
                "user_host": "search_api",
                "sql_command": "SELECT"
            },
            # 笛卡尔积查询
            {
                "query_text": "SELECT u.name, p.title FROM users u, posts p WHERE u.id > 1000 AND p.user_id > 500 ORDER BY u.name, p.title LIMIT 50",
                "execution_time": 7.8 + random.uniform(-2, 2),
                "rows_examined": 800000 + random.randint(-150000, 150000),
                "rows_sent": 50,
                "user_host": "data_export",
                "sql_command": "SELECT"
            },
            # 大量数据分页查询
            {
                "query_text": "SELECT * FROM audit_logs WHERE action_type IN ('login', 'logout', 'update') AND created_at >= '2023-01-01' ORDER BY created_at DESC LIMIT 1000 OFFSET 50000",
                "execution_time": 3.2 + random.uniform(-0.7, 0.7),
                "rows_examined": 75000 + random.randint(-15000, 15000),
                "rows_sent": 1000,
                "user_host": "audit_system",
                "sql_command": "SELECT"
            },
            # 复杂WHERE条件
            {
                "query_text": "DELETE FROM notifications WHERE (user_id IN (SELECT id FROM users WHERE last_login < '2023-06-01') OR created_at < '2023-01-01') AND type NOT IN ('system', 'important') AND status = 'unread'",
                "execution_time": 4.7 + random.uniform(-1, 1),
                "rows_examined": 300000 + random.randint(-60000, 60000),
                "rows_sent": 0,
                "user_host": "cleanup_service",
                "sql_command": "DELETE"
            }
        ]

        captured_queries = []
        for mock_query in mock_slow_queries:
            if mock_query["execution_time"] >= threshold_seconds:
                query_hash = self._generate_query_hash(mock_query["query_text"])
                captured_queries.append({
                    **mock_query,
                    "query_hash": query_hash,
                    "database_id": database_id,
                    "lock_time": 0.0,
                    "timestamp": datetime.now()
                })

        return captured_queries

    def analyze_query_patterns(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        """
        分析查询模式 - 增强版
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 获取实际的慢查询数据进行分析
        slow_queries = self.db.query(SlowQuery)\
            .filter(
                SlowQuery.database_id == database_id,
                SlowQuery.timestamp >= start_date,
                SlowQuery.timestamp <= end_date
            )\
            .all()

        if not slow_queries:
            # 如果没有实际数据，返回增强的mock数据
            return self._generate_enhanced_mock_patterns()

        # 实际数据分析
        return self._analyze_real_query_patterns(slow_queries)

    def _analyze_real_query_patterns(self, slow_queries: List[SlowQuery]) -> Dict[str, Any]:
        """分析真实的查询模式数据"""
        total_queries = len(slow_queries)
        total_time = sum(query.execution_time for query in slow_queries)
        avg_time = total_time / total_queries if total_queries > 0 else 0

        # 分析查询模式
        patterns = {}
        table_usage = {}

        for query in slow_queries:
            # 提取查询模式
            pattern = self._extract_query_pattern(query.query_text)
            if pattern not in patterns:
                patterns[pattern] = {
                    "count": 0,
                    "total_time": 0,
                    "queries": []
                }

            patterns[pattern]["count"] += 1
            patterns[pattern]["total_time"] += query.execution_time
            patterns[pattern]["queries"].append(query.query_text[:100] + "...")

            # 提取表名
            tables = self._extract_table_names(query.query_text)
            for table in tables:
                if table not in table_usage:
                    table_usage[table] = {"count": 0, "total_time": 0}
                table_usage[table]["count"] += 1
                table_usage[table]["total_time"] += query.execution_time

        # 格式化结果
        most_common_patterns = []
        for pattern, data in patterns.items():
            most_common_patterns.append({
                "pattern": pattern,
                "count": data["count"],
                "avg_time": round(data["total_time"] / data["count"], 2),
                "impact_score": self._calculate_pattern_impact(pattern, data)
            })

        # 按影响程度排序
        most_common_patterns.sort(key=lambda x: x["impact_score"], reverse=True)

        top_tables = []
        for table, usage in table_usage.items():
            top_tables.append({
                "table": table,
                "query_count": usage["count"],
                "avg_time": round(usage["total_time"] / usage["count"], 2),
                "total_time": round(usage["total_time"], 2)
            })

        top_tables.sort(key=lambda x: x["total_time"], reverse=True)

        # 生成基于真实数据的建议
        recommendations = []
        if most_common_patterns:
            top_pattern = most_common_patterns[0]
            if "JOIN" in top_pattern["pattern"]:
                recommendations.append("优化JOIN查询，考虑添加索引或调整查询结构")
            if "ORDER BY" in top_pattern["pattern"]:
                recommendations.append("为排序字段添加索引以提升性能")
        
        if top_tables:
            top_table = top_tables[0]
            recommendations.append(f"重点优化表 {top_table['table']} 的查询性能")
        
        # 默认建议
        if not recommendations:
            recommendations = [
                "为高频查询的WHERE条件列添加索引",
                "定期执行ANALYZE更新表统计信息",
                "考虑查询重写以提升性能"
            ]

        return {
            "total_slow_queries": total_queries,
            "avg_execution_time": round(avg_time, 2),
            "most_common_patterns": most_common_patterns[:10],  # Top 10 patterns
            "top_tables": top_tables[:10],  # Top 10 tables
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _generate_enhanced_mock_patterns(self) -> Dict[str, Any]:
        """生成PostgreSQL增强的mock查询模式数据 - 演示版"""
        import random
        import hashlib
        from datetime import datetime

        # 使用时间作为种子的一部分，确保数据有一定变化但相对稳定
        seed = int(hashlib.md5(f"patterns_{datetime.now().hour}".encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)

        # 生成更丰富的查询模式数据
        patterns_data = [
            {
                "pattern": "复杂多表JOIN查询",
                "count": 67 + random.randint(-10, 10),
                "avg_time": 3.2 + random.uniform(-0.5, 0.5),
                "sample_query": "SELECT u.name, u.email, p.title, c.name FROM users u JOIN posts p ON u.id = p.user_id JOIN categories c ON p.category_id = c.id WHERE u.status = 'active' ORDER BY p.created_at DESC LIMIT 50",
                "impact_score": 85 + random.randint(-5, 5),
                "recommended_index": "复合索引: (user_id, created_at) ON posts",
                "postgres_specific": True,
                "bottlenecks": ["缺少复合索引", "JOIN顺序优化"]
            },
            {
                "pattern": "窗口函数排序查询",
                "count": 52 + random.randint(-8, 8),
                "avg_time": 4.1 + random.uniform(-0.8, 0.8),
                "sample_query": "SELECT id, name, department, salary, ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank_in_dept FROM employees WHERE active = true",
                "impact_score": 88 + random.randint(-4, 4),
                "recommended_index": "复合索引: (department, salary) ON employees",
                "postgres_specific": True,
                "bottlenecks": ["窗口函数性能", "排序操作"]
            },
            {
                "pattern": "递归CTE查询",
                "count": 41 + random.randint(-6, 6),
                "avg_time": 3.8 + random.uniform(-0.7, 0.7),
                "sample_query": "WITH RECURSIVE category_tree AS (SELECT id, name, parent_id, 0 as level FROM categories WHERE parent_id IS NULL UNION ALL SELECT c.id, c.name, c.parent_id, ct.level + 1 FROM categories c JOIN category_tree ct ON c.parent_id = ct.id) SELECT * FROM category_tree ORDER BY level, name",
                "impact_score": 82 + random.randint(-6, 6),
                "recommended_index": "索引: (parent_id) ON categories",
                "postgres_specific": True,
                "bottlenecks": ["递归查询深度", "缺少父子索引"]
            },
            {
                "pattern": "JSON字段查询",
                "count": 35 + random.randint(-5, 5),
                "avg_time": 2.9 + random.uniform(-0.4, 0.4),
                "sample_query": "SELECT * FROM products WHERE metadata->>'category' = 'electronics' AND (metadata->'price')::numeric BETWEEN 100 AND 1000 AND metadata->'specs'->>'brand' IN ('Apple', 'Samsung')",
                "impact_score": 75 + random.randint(-8, 8),
                "recommended_index": "GIN索引: ON products USING gin(metadata)",
                "postgres_specific": True,
                "bottlenecks": ["JSON操作性能", "缺少GIN索引"]
            },
            {
                "pattern": "数组包含查询",
                "count": 29 + random.randint(-4, 4),
                "avg_time": 3.3 + random.uniform(-0.6, 0.6),
                "sample_query": "SELECT * FROM articles WHERE tags && ARRAY['postgresql', 'database', 'tutorial'] AND published = true AND created_at >= '2023-01-01' ORDER BY view_count DESC",
                "impact_score": 79 + random.randint(-7, 7),
                "recommended_index": "GIN索引: ON articles USING gin(tags)",
                "postgres_specific": True,
                "bottlenecks": ["数组操作性能", "标签搜索效率"]
            },
            {
                "pattern": "范围查询无索引",
                "count": 58 + random.randint(-12, 12),
                "avg_time": 2.6 + random.uniform(-0.4, 0.4),
                "sample_query": "SELECT * FROM orders WHERE created_at BETWEEN '2023-06-01' AND '2023-06-30' AND total_amount > 500 AND status IN ('completed', 'shipped') ORDER BY created_at DESC",
                "impact_score": 78 + random.randint(-6, 6),
                "recommended_index": "复合索引: (created_at, total_amount, status) ON orders",
                "postgres_specific": False,
                "bottlenecks": ["全表扫描", "范围查询性能"]
            },
            {
                "pattern": "模糊文本搜索",
                "count": 44 + random.randint(-8, 8),
                "avg_time": 4.8 + random.uniform(-1, 1),
                "sample_query": "SELECT * FROM products WHERE LOWER(name) LIKE '%wireless%' OR LOWER(description) LIKE '%bluetooth%' AND category_id IN (1,2,3) ORDER BY price ASC",
                "impact_score": 82 + random.randint(-5, 5),
                "recommended_index": "全文索引: ON products USING gin(to_tsvector('english', name || ' ' || description))",
                "postgres_specific": True,
                "bottlenecks": ["LIKE操作性能", "文本搜索效率"]
            },
            {
                "pattern": "子查询性能问题",
                "count": 33 + random.randint(-6, 6),
                "avg_time": 3.7 + random.uniform(-0.8, 0.8),
                "sample_query": "UPDATE products SET stock_quantity = stock_quantity - 1 WHERE category_id IN (SELECT id FROM categories WHERE parent_id IN (SELECT id FROM departments WHERE active = true)) AND stock_quantity > 0",
                "impact_score": 76 + random.randint(-7, 7),
                "recommended_index": "多列索引: (parent_id, active) ON departments, (category_id) ON products",
                "postgres_specific": False,
                "bottlenecks": ["子查询优化", "IN操作性能"]
            },
            {
                "pattern": "聚合查询无索引",
                "count": 39 + random.randint(-7, 7),
                "avg_time": 5.2 + random.uniform(-1.2, 1.2),
                "sample_query": "SELECT DATE(created_at), COUNT(*), SUM(amount), AVG(amount), MIN(amount), MAX(amount) FROM transactions WHERE created_at >= '2023-01-01' AND type = 'purchase' GROUP BY DATE(created_at) ORDER BY DATE(created_at) DESC LIMIT 30",
                "impact_score": 88 + random.randint(-4, 4),
                "recommended_index": "复合索引: (type, created_at) ON transactions",
                "postgres_specific": False,
                "bottlenecks": ["聚合操作性能", "GROUP BY效率"]
            },
            {
                "pattern": "分页查询性能",
                "count": 48 + random.randint(-9, 9),
                "avg_time": 3.9 + random.uniform(-0.7, 0.7),
                "sample_query": "SELECT * FROM audit_logs WHERE action IN ('login', 'update', 'delete') AND user_id > 1000 ORDER BY created_at DESC LIMIT 100 OFFSET 5000",
                "impact_score": 74 + random.randint(-8, 8),
                "recommended_index": "复合索引: (action, created_at) ON audit_logs, (user_id) ON audit_logs",
                "postgres_specific": False,
                "bottlenecks": ["OFFSET性能", "大结果集分页"]
            }
        ]

        # 按影响程度排序
        patterns_data.sort(key=lambda x: x["impact_score"], reverse=True)

        # 生成表使用统计
        tables_data = [
            {
                "table": "users",
                "query_count": 89 + random.randint(-15, 15),
                "avg_time": 2.3 + random.uniform(-0.3, 0.3),
                "total_time": 204.7 + random.uniform(-30, 30),
                "index_recommendations": ["B-tree on email", "GIN on metadata", "复合索引 on (status, created_at)"],
                "bottlenecks": ["缺少复合索引", "JSON查询性能"]
            },
            {
                "table": "orders",
                "query_count": 67 + random.randint(-12, 12),
                "avg_time": 3.1 + random.uniform(-0.4, 0.4),
                "total_time": 207.7 + random.uniform(-40, 40),
                "index_recommendations": ["复合索引 on (created_at, status)", "B-tree on user_id", "B-tree on total_amount"],
                "bottlenecks": ["范围查询慢", "JOIN性能"]
            },
            {
                "table": "products",
                "query_count": 54 + random.randint(-10, 10),
                "avg_time": 2.7 + random.uniform(-0.4, 0.4),
                "total_time": 145.8 + random.uniform(-25, 25),
                "index_recommendations": ["GIN on tags", "GIN on metadata", "B-tree on category_id"],
                "bottlenecks": ["JSON操作慢", "数组查询性能"]
            },
            {
                "table": "articles",
                "query_count": 43 + random.randint(-8, 8),
                "avg_time": 1.9 + random.uniform(-0.3, 0.3),
                "total_time": 81.7 + random.uniform(-15, 15),
                "index_recommendations": ["GIN on tags", "B-tree on published", "B-tree on view_count"],
                "bottlenecks": ["标签搜索慢", "排序性能"]
            },
            {
                "table": "logs",
                "query_count": 38 + random.randint(-7, 7),
                "avg_time": 1.6 + random.uniform(-0.2, 0.2),
                "total_time": 60.8 + random.uniform(-10, 10),
                "index_recommendations": ["BRIN on created_at", "B-tree on level", "复合索引 on (source, created_at)"],
                "bottlenecks": ["时间范围查询", "大表扫描"]
            },
            {
                "table": "categories",
                "query_count": 31 + random.randint(-6, 6),
                "avg_time": 1.4 + random.uniform(-0.2, 0.2),
                "total_time": 43.4 + random.uniform(-8, 8),
                "index_recommendations": ["B-tree on parent_id", "复合索引 on (parent_id, active)"],
                "bottlenecks": ["层级查询慢", "递归查询性能"]
            },
            {
                "table": "transactions",
                "query_count": 28 + random.randint(-5, 5),
                "avg_time": 2.1 + random.uniform(-0.3, 0.3),
                "total_time": 58.8 + random.uniform(-12, 12),
                "index_recommendations": ["复合索引 on (type, created_at)", "B-tree on amount"],
                "bottlenecks": ["聚合查询慢", "范围查询性能"]
            }
        ]

        # 按总时间排序
        tables_data.sort(key=lambda x: x["total_time"], reverse=True)

        # 计算总数
        total_queries = sum(p["count"] for p in patterns_data)
        avg_time = sum(p["count"] * p["avg_time"] for p in patterns_data) / total_queries if total_queries > 0 else 0

        # 生成总体建议
        recommendations = [
            "为高频查询的WHERE条件列添加B-tree索引",
            "考虑为JSON字段创建GIN索引以提升查询性能",
            "优化复杂JOIN查询的表连接顺序",
            "为时间范围查询添加BRIN索引",
            "定期执行VACUUM ANALYZE以更新统计信息",
            "考虑对大表进行分区以提升查询性能"
        ]

        return {
            "total_slow_queries": total_queries,
            "avg_execution_time": round(avg_time, 2),
            "most_common_patterns": patterns_data[:12],  # Top 12 patterns
            "top_tables": tables_data[:8],  # Top 8 tables
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "postgres_specific_insights": {
                "json_operations_count": sum(1 for p in patterns_data if p.get("postgres_specific") and "JSON" in p["pattern"]),
                "array_operations_count": sum(1 for p in patterns_data if p.get("postgres_specific") and "数组" in p["pattern"]),
                "window_functions_count": sum(1 for p in patterns_data if "窗口函数" in p["pattern"]),
                "cte_usage_count": sum(1 for p in patterns_data if "CTE" in p["pattern"] or "递归" in p["pattern"]),
                "gin_index_opportunities": len([p for p in patterns_data if "GIN" in p.get("recommended_index", "")]),
                "brin_index_opportunities": len([p for p in patterns_data if "BRIN" in p.get("recommended_index", "")]),
                "vacuum_recommendations": random.randint(1, 4),
                "partitioning_opportunities": random.randint(0, 3)
            },
            "performance_summary": {
                "critical_queries": len([p for p in patterns_data if p["impact_score"] > 80]),
                "high_impact_queries": len([p for p in patterns_data if 70 <= p["impact_score"] <= 80]),
                "medium_impact_queries": len([p for p in patterns_data if 50 <= p["impact_score"] < 70]),
                "total_optimization_potential": round(sum(p["impact_score"] * p["count"] for p in patterns_data) / 100, 1)
            }
        }

    def _extract_query_pattern(self, query_text: str) -> str:
        """提取PostgreSQL查询模式"""
        query = query_text.upper().strip()

        if query.startswith("SELECT"):
            if "JOIN" in query and "ORDER BY" in query:
                return "SELECT with JOIN and ORDER BY"
            elif "JOIN" in query:
                return "SELECT with JOIN"
            elif "ORDER BY" in query:
                return "SELECT with ORDER BY"
            elif "GROUP BY" in query:
                return "SELECT with GROUP BY"
            elif "HAVING" in query:
                return "SELECT with HAVING"
            elif "DISTINCT" in query:
                return "SELECT with DISTINCT"
            elif "LIKE" in query or "ILIKE" in query:
                return "SELECT with text search"
            elif "IN (" in query:
                return "SELECT with IN clause"
            elif "EXISTS" in query:
                return "SELECT with EXISTS"
            elif "UNION" in query:
                return "SELECT with UNION"
            elif "INTERSECT" in query:
                return "SELECT with INTERSECT"
            elif "EXCEPT" in query:
                return "SELECT with EXCEPT"
            elif "WINDOW" in query or "OVER (" in query:
                return "SELECT with window functions"
            elif "CTE" in query or "WITH " in query:
                return "SELECT with CTE"
            else:
                return "Simple SELECT"
        elif query.startswith("UPDATE"):
            if "FROM" in query or "JOIN" in query:
                return "UPDATE with FROM/JOIN"
            elif "RETURNING" in query:
                return "UPDATE with RETURNING"
            else:
                return "Simple UPDATE"
        elif query.startswith("INSERT"):
            if "RETURNING" in query:
                return "INSERT with RETURNING"
            elif "ON CONFLICT" in query:
                return "INSERT with ON CONFLICT"
            elif "SELECT" in query:
                return "INSERT with SELECT"
            else:
                return "Simple INSERT"
        elif query.startswith("DELETE"):
            if "USING" in query or "JOIN" in query:
                return "DELETE with USING/JOIN"
            elif "RETURNING" in query:
                return "DELETE with RETURNING"
            else:
                return "Simple DELETE"
        elif query.startswith("WITH"):
            return "CTE (Common Table Expression)"
        else:
            return "Other"

    def _extract_table_names(self, query_text: str) -> List[str]:
        """提取查询中的表名"""
        import re

        # 简单的表名提取逻辑
        query = query_text.upper()

        # 匹配 FROM、JOIN、UPDATE、INSERT INTO 后的表名
        patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)'
        ]

        tables = []
        for pattern in patterns:
            matches = re.findall(pattern, query)
            tables.extend(matches)

        # 去重并返回小写表名
        return list(set(table.lower() for table in tables))

    def _calculate_pattern_impact(self, pattern: str, data: Dict) -> int:
        """计算查询模式的影響程度"""
        base_score = data["count"] * 10  # 数量权重
        time_score = data["total_time"] * 5  # 执行时间权重

        # 模式复杂度权重
        complexity_multipliers = {
            "SELECT with JOIN and ORDER BY": 1.5,
            "UPDATE with subquery": 1.4,
            "DELETE with JOIN": 1.3,
            "SELECT with complex WHERE": 1.2,
            "INSERT with SELECT": 1.1
        }

        multiplier = complexity_multipliers.get(pattern, 1.0)

        return int((base_score + time_score) * multiplier)

    def generate_optimization_suggestions(self, query_text: str, execution_time: float, rows_examined: int) -> Dict[str, Any]:
        """
        生成智能优化建议 - 增强版
        """
        suggestions = []
        query_upper = query_text.upper()

        # 高级索引建议
        index_suggestions = self._analyze_index_opportunities(query_text, execution_time, rows_examined)
        suggestions.extend(index_suggestions)

        # JOIN 优化建议
        if "JOIN" in query_upper:
            join_suggestions = self._analyze_join_performance(query_text, execution_time, rows_examined)
            suggestions.extend(join_suggestions)

        # 子查询优化建议
        if ("(" in query_text and "SELECT" in query_upper) or "IN (" in query_upper:
            subquery_suggestions = self._analyze_subquery_performance(query_text, execution_time)
            suggestions.extend(subquery_suggestions)

        # ORDER BY 优化建议
        if "ORDER BY" in query_upper:
            order_suggestions = self._analyze_order_by_performance(query_text, execution_time, rows_examined)
            suggestions.extend(order_suggestions)

        # GROUP BY 优化建议
        if "GROUP BY" in query_upper:
            group_suggestions = self._analyze_group_by_performance(query_text, execution_time, rows_examined)
            suggestions.extend(group_suggestions)

        # LIKE 查询优化建议
        if "LIKE" in query_upper:
            like_suggestions = self._analyze_like_performance(query_text, execution_time)
            suggestions.extend(like_suggestions)

        # LIMIT 和 OFFSET 优化建议
        if "LIMIT" in query_upper:
            limit_suggestions = self._analyze_limit_performance(query_text, execution_time, rows_examined)
            suggestions.extend(limit_suggestions)

        # 计算查询复杂度
        complexity_score = self._calculate_query_complexity(query_text, execution_time, rows_examined)
        efficiency_score = self._calculate_query_efficiency(execution_time, rows_examined)

        # 按优先级排序建议
        suggestions.sort(key=lambda x: self._get_suggestion_priority(x), reverse=True)

        return {
            "query_analysis": {
                "complexity_score": complexity_score,
                "efficiency_score": efficiency_score,
                "performance_rating": self._get_performance_rating(complexity_score, efficiency_score)
            },
            "suggestions": suggestions[:5],  # 返回Top 5建议
            "priority_score": self._calculate_priority_score(suggestions, execution_time),
            "estimated_improvement": self._estimate_total_improvement(suggestions)
        }

    def _analyze_index_opportunities(self, query_text: str, execution_time: float, rows_examined: int) -> List[Dict]:
        """分析PostgreSQL索引优化机会"""
        suggestions = []
        query_upper = query_text.upper()

        # WHERE 条件索引建议
        if "WHERE" in query_upper and execution_time > 1.0:
            where_conditions = self._extract_where_conditions(query_text)
            for condition in where_conditions[:3]:  # 最多建议3个索引
                # 根据条件类型选择合适的索引类型
                index_type = self._recommend_index_type(query_text, condition)
                suggestions.append({
                    "type": "btree_index" if index_type == "btree" else f"{index_type}_index",
                    "title": f"为 {condition} 添加{self._get_index_type_name(index_type)}索引",
                    "description": f"WHERE 条件 {condition} 可能需要{self._get_index_type_name(index_type)}索引来提升查询性能",
                    "impact": "high" if execution_time > 3.0 else "medium",
                    "estimated_improvement": "50-80% 性能提升",
                    "sql_suggestion": self._generate_postgres_index_sql(index_type, "table", condition),
                    "effort": "low",
                    "index_type": index_type
                })

        # JOIN 条件索引建议
        if "JOIN" in query_upper and "ON" in query_upper:
            join_conditions = self._extract_join_conditions(query_text)
            for condition in join_conditions:
                suggestions.append({
                    "type": "join_index",
                    "title": f"为 JOIN 条件添加B-tree索引",
                    "description": f"JOIN 条件 {condition} 缺少索引，可能导致性能问题",
                    "impact": "high",
                    "estimated_improvement": "40-70% 性能提升",
                    "sql_suggestion": self._generate_postgres_index_sql("btree", "table", condition),
                    "effort": "medium",
                    "index_type": "btree"
                })

        # 全文搜索索引建议
        if ("LIKE" in query_upper or "ILIKE" in query_upper) and "%" in query_text:
            if execution_time > 2.0:
                suggestions.append({
                    "type": "gin_index",
                    "title": "为全文搜索添加GIN索引",
                    "description": "查询包含模糊匹配，建议使用GIN索引进行全文搜索优化",
                    "impact": "high",
                    "estimated_improvement": "70-90% 性能提升",
                    "sql_suggestion": "CREATE INDEX CONCURRENTLY idx_text_search ON table USING gin(to_tsvector('english', text_column));",
                    "effort": "medium",
                    "index_type": "gin"
                })

        # 数组操作索引建议
        if "&&" in query_text or "@>" in query_text or "<@" in query_text:
            suggestions.append({
                "type": "gin_index",
                "title": "为数组操作添加GIN索引",
                "description": "查询包含数组操作，建议使用GIN索引优化",
                "impact": "medium",
                "estimated_improvement": "60-80% 性能提升",
                "sql_suggestion": "CREATE INDEX CONCURRENTLY idx_array_ops ON table USING gin(array_column);",
                "effort": "medium",
                "index_type": "gin"
            })

        # JSON操作索引建议
        if "->" in query_text or "->>" in query_text or "#>" in query_text:
            suggestions.append({
                "type": "gin_index",
                "title": "为JSON操作添加GIN索引",
                "description": "查询包含JSON操作，建议使用GIN索引优化",
                "impact": "medium",
                "estimated_improvement": "50-75% 性能提升",
                "sql_suggestion": "CREATE INDEX CONCURRENTLY idx_json_ops ON table USING gin(json_column);",
                "effort": "medium",
                "index_type": "gin"
            })

        return suggestions

    def _recommend_index_type(self, query_text: str, condition: str) -> str:
        """根据查询条件推荐索引类型"""
        query_upper = query_text.upper()

        # 全文搜索推荐GIN索引
        if ("LIKE" in query_upper or "ILIKE" in query_upper) and "%" in query_text:
            return "gin"

        # 数组操作推荐GIN索引
        if "&&" in query_text or "@>" in query_text or "<@" in query_text:
            return "gin"

        # JSON操作推荐GIN索引
        if "->" in query_text or "->>" in query_text or "#>" in query_text:
            return "gin"

        # 几何数据推荐GiST索引
        if "&&" in query_text or "@" in query_text or "~" in query_text:
            return "gist"

        # 范围查询推荐BRIN索引（对于有序数据）
        if "BETWEEN" in query_upper or ("<" in condition and ">" in condition):
            return "brin"

        # 默认使用B-tree索引
        return "btree"

    def _get_index_type_name(self, index_type: str) -> str:
        """获取索引类型的中文名称"""
        type_names = {
            "btree": "B-tree",
            "hash": "Hash",
            "gin": "GIN",
            "gist": "GiST",
            "spgist": "SP-GiST",
            "brin": "BRIN"
        }
        return type_names.get(index_type, index_type.upper())

    def _generate_postgres_index_sql(self, index_type: str, table_name: str, column: str) -> str:
        """生成PostgreSQL索引创建SQL"""
        index_name = f"idx_{table_name}_{column.lower().replace('.', '_')}"

        if index_type == "btree":
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} ({column});"
        elif index_type == "hash":
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING hash ({column});"
        elif index_type == "gin":
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING gin ({column});"
        elif index_type == "gist":
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING gist ({column});"
        elif index_type == "brin":
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} USING brin ({column});"
        else:
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} ({column});"

    def _analyze_join_performance(self, query_text: str, execution_time: float, rows_examined: int) -> List[Dict]:
        """分析JOIN性能"""
        suggestions = []
        query_upper = query_text.upper()

        join_count = query_upper.count("JOIN")
        if join_count > 2 and execution_time > 2.0:
            suggestions.append({
                "type": "join_optimization",
                "title": "优化多表JOIN",
                "description": f"查询包含 {join_count} 个JOIN操作，考虑优化JOIN顺序或使用临时表",
                "impact": "high",
                "estimated_improvement": "30-60% 性能提升",
                "sql_suggestion": "考虑使用STRAIGHT_JOIN强制JOIN顺序，或将复杂JOIN拆分为多个查询",
                "effort": "high"
            })

        # 检查是否有交叉JOIN
        if "JOIN" in query_upper and "WHERE" not in query_upper:
            suggestions.append({
                "type": "cross_join",
                "title": "避免笛卡尔积",
                "description": "查询可能产生笛卡尔积，建议添加合适的JOIN条件",
                "impact": "critical",
                "estimated_improvement": "80-95% 性能提升",
                "sql_suggestion": "在JOIN后添加WHERE条件或ON条件来限制结果集",
                "effort": "medium"
            })

        return suggestions

    def _analyze_subquery_performance(self, query_text: str, execution_time: float) -> List[Dict]:
        """分析子查询性能"""
        suggestions = []
        query_upper = query_text.upper()

        subquery_count = query_text.count("(") - query_text.count("IN (")
        if subquery_count > 0 and execution_time > 1.5:
            suggestions.append({
                "type": "subquery_optimization",
                "title": "优化子查询",
                "description": f"查询包含 {subquery_count} 个子查询，考虑重写为JOIN或使用临时表",
                "impact": "medium",
                "estimated_improvement": "20-50% 性能提升",
                "sql_suggestion": "将子查询重写为LEFT JOIN，或使用EXISTS代替IN子查询",
                "effort": "medium"
            })

        # IN子查询优化
        if "IN (" in query_upper and "SELECT" in query_upper:
            suggestions.append({
                "type": "in_subquery",
                "title": "优化IN子查询",
                "description": "IN子查询可能影响性能，考虑使用JOIN或EXISTS代替",
                "impact": "medium",
                "estimated_improvement": "30-50% 性能提升",
                "sql_suggestion": "使用INNER JOIN或EXISTS代替IN子查询",
                "effort": "low"
            })

        return suggestions

    def _analyze_order_by_performance(self, query_text: str, execution_time: float, rows_examined: int) -> List[Dict]:
        """分析ORDER BY性能"""
        suggestions = []
        query_upper = query_text.upper()

        if "ORDER BY" in query_upper and execution_time > 2.0:
            order_columns = self._extract_order_columns(query_text)
            suggestions.append({
                "type": "order_by_index",
                "title": "为排序列添加索引",
                "description": f"ORDER BY 列 {', '.join(order_columns[:3])} 需要索引来提升排序性能",
                "impact": "high" if rows_examined > 10000 else "medium",
                "estimated_improvement": "40-70% 性能提升",
                "sql_suggestion": f"CREATE INDEX idx_order_{'_'.join(order_columns[:3])} ON table({', '.join(order_columns[:3])});",
                "effort": "low"
            })

        return suggestions

    def _analyze_group_by_performance(self, query_text: str, execution_time: float, rows_examined: int) -> List[Dict]:
        """分析GROUP BY性能"""
        suggestions = []
        query_upper = query_text.upper()

        if "GROUP BY" in query_upper and execution_time > 1.5:
            group_columns = self._extract_group_columns(query_text)
            suggestions.append({
                "type": "group_by_index",
                "title": "为分组列添加索引",
                "description": f"GROUP BY 列 {', '.join(group_columns[:3])} 需要索引来提升分组性能",
                "impact": "medium",
                "estimated_improvement": "25-45% 性能提升",
                "sql_suggestion": f"CREATE INDEX idx_group_{'_'.join(group_columns[:3])} ON table({', '.join(group_columns[:3])});",
                "effort": "low"
            })

        return suggestions

    def _analyze_like_performance(self, query_text: str, execution_time: float) -> List[Dict]:
        """分析LIKE查询性能"""
        suggestions = []
        query_upper = query_text.upper()

        if "LIKE" in query_upper and execution_time > 1.0:
            if "'%" in query_text:  # 前缀匹配
                suggestions.append({
                    "type": "like_prefix",
                    "title": "优化前缀LIKE查询",
                    "description": "LIKE查询以%开头无法使用索引，考虑使用全文索引或重构查询",
                    "impact": "high",
                    "estimated_improvement": "60-85% 性能提升",
                    "sql_suggestion": "使用全文索引或考虑其他搜索方案",
                    "effort": "high"
                })

        return suggestions

    def _analyze_limit_performance(self, query_text: str, execution_time: float, rows_examined: int) -> List[Dict]:
        """分析LIMIT性能"""
        suggestions = []
        query_upper = query_text.upper()

        if "LIMIT" in query_upper and "OFFSET" in query_upper and execution_time > 1.0:
            suggestions.append({
                "type": "limit_offset",
                "title": "优化分页查询",
                "description": "OFFSET分页在大结果集上性能较差，考虑使用游标或记录上次位置",
                "impact": "medium",
                "estimated_improvement": "50-75% 性能提升",
                "sql_suggestion": "使用WHERE id > last_id代替OFFSET，或使用游标分页",
                "effort": "medium"
            })

        return suggestions

    def _calculate_query_complexity(self, query_text: str, execution_time: float, rows_examined: int) -> float:
        """计算查询复杂度评分"""
        complexity = 0

        # 执行时间权重
        complexity += min(40, execution_time * 10)

        # 检查行数权重
        complexity += min(30, rows_examined / 10000)

        # SQL复杂度权重
        query_upper = query_text.upper()
        if "JOIN" in query_upper: complexity += 10
        if "SUBQUERY" in query_upper or "(" in query_text: complexity += 8
        if "UNION" in query_upper: complexity += 12
        if "GROUP BY" in query_upper: complexity += 6
        if "ORDER BY" in query_upper: complexity += 4
        if "DISTINCT" in query_upper: complexity += 5

        return min(100, complexity)

    def _calculate_query_efficiency(self, execution_time: float, rows_examined: int) -> float:
        """计算查询效率评分"""
        if rows_examined == 0:
            return 100

        # 每行数据的处理时间
        time_per_row = execution_time / rows_examined

        # 理想情况下，每行应该在0.001秒内处理
        ideal_time_per_row = 0.001

        if time_per_row <= ideal_time_per_row:
            return 100
        elif time_per_row <= ideal_time_per_row * 10:
            return 80
        elif time_per_row <= ideal_time_per_row * 50:
            return 60
        elif time_per_row <= ideal_time_per_row * 100:
            return 40
        else:
            return max(0, 100 - (time_per_row / ideal_time_per_row) * 2)

    def _get_performance_rating(self, complexity: float, efficiency: float) -> str:
        """获取性能评级"""
        avg_score = (complexity + (100 - efficiency)) / 2

        if avg_score < 20: return "excellent"
        elif avg_score < 40: return "good"
        elif avg_score < 60: return "fair"
        elif avg_score < 80: return "poor"
        else: return "critical"

    def _get_suggestion_priority(self, suggestion: Dict) -> int:
        """获取建议优先级"""
        base_priority = {"critical": 100, "high": 75, "medium": 50, "low": 25}.get(suggestion.get("impact", "low"), 25)
        effort_penalty = {"high": 20, "medium": 10, "low": 0}.get(suggestion.get("effort", "medium"), 10)

        return base_priority - effort_penalty

    def _estimate_total_improvement(self, suggestions: List[Dict]) -> str:
        """估算总改进效果"""
        if not suggestions:
            return "0%"

        # 计算平均改进百分比
        improvements = []
        for suggestion in suggestions:
            improvement_text = suggestion.get("estimated_improvement", "0%")
            if "-" in improvement_text:
                # 范围格式，如 "30-60%"
                parts = improvement_text.replace("%", "").split("-")
                avg = (int(parts[0]) + int(parts[1])) / 2
                improvements.append(avg)
            elif "%" in improvement_text:
                improvements.append(int(improvement_text.replace("%", "")))
            else:
                improvements.append(0)

        if not improvements:
            return "0%"

        avg_improvement = sum(improvements) / len(improvements)
        return f"{int(avg_improvement)}%"

    def _extract_where_conditions(self, query_text: str) -> List[str]:
        """提取WHERE条件中的列名"""
        import re

        # 简单提取WHERE条件中的列
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+(?:GROUP|ORDER|LIMIT|$))', query_text.upper(), re.DOTALL)
        if not where_match:
            return []

        where_clause = where_match.group(1)

        # 提取列名模式
        column_patterns = [
            r'(\w+\.\w+)',
            r'(\w+)\s*[=<>!]',
            r'(\w+)\s+LIKE',
            r'(\w+)\s+IN\s*\(',
            r'(\w+)\s+BETWEEN'
        ]

        columns = []
        for pattern in column_patterns:
            matches = re.findall(pattern, where_clause)
            columns.extend(matches)

        return list(set(columns))[:5]  # 最多返回5个

    def _extract_join_conditions(self, query_text: str) -> List[str]:
        """提取JOIN条件中的列名"""
        import re

        # 提取ON条件
        on_matches = re.findall(r'ON\s+(.*?)(?:\s+(?:WHERE|GROUP|ORDER|LIMIT|JOIN|$))', query_text.upper(), re.DOTALL)

        columns = []
        for on_clause in on_matches:
            column_matches = re.findall(r'(\w+\.\w+)\s*=\s*(\w+\.\w+)', on_clause)
            for match in column_matches:
                columns.extend(match)

        return list(set(columns))[:3]  # 最多返回3个

    def _extract_order_columns(self, query_text: str) -> List[str]:
        """提取ORDER BY列名"""
        import re

        order_match = re.search(r'ORDER BY\s+(.*?)(?:\s+(?:LIMIT|$))', query_text.upper())
        if not order_match:
            return []

        order_clause = order_match.group(1)
        columns = re.findall(r'(\w+\.\w+|\w+)', order_clause)

        return list(set(columns))[:3]

    def _extract_group_columns(self, query_text: str) -> List[str]:
        """提取GROUP BY列名"""
        import re

        group_match = re.search(r'GROUP BY\s+(.*?)(?:\s+(?:ORDER|HAVING|LIMIT|$))', query_text.upper())
        if not group_match:
            return []

        group_clause = group_match.group(1)
        columns = re.findall(r'(\w+\.\w+|\w+)', group_clause)

        return list(set(columns))[:3]

    def _generate_query_hash(self, query_text: str) -> str:
        """生成查询哈希"""
        # 标准化查询（去除空格、换行符等）
        normalized = ' '.join(query_text.split()).lower()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _calculate_priority_score(self, suggestions: List[Dict], execution_time: float) -> float:
        """计算优先级评分"""
        base_score = min(100, execution_time * 10)

        # 根据建议类型调整评分
        for suggestion in suggestions:
            if suggestion["impact"] == "high":
                base_score += 20
            elif suggestion["impact"] == "medium":
                base_score += 10

        return min(100, base_score)

    def save_slow_query(self, slow_query_data: Dict[str, Any]) -> SlowQuery:
        """
        保存慢查询记录
        """
        slow_query = SlowQuery(**slow_query_data)
        self.db.add(slow_query)
        self.db.commit()
        self.db.refresh(slow_query)
        return slow_query

    def get_slow_queries(self, database_id: int, limit: int = 100, offset: int = 0) -> List[SlowQuery]:
        """
        获取慢查询列表
        """
        return self.db.query(SlowQuery)\
            .filter(SlowQuery.database_id == database_id)\
            .order_by(SlowQuery.timestamp.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

    def get_query_statistics(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        """
        获取查询统计信息
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Mock statistics
        return {
            "period": f"{days}天",
            "total_queries": 15420,
            "slow_queries": 287,
            "slow_query_percentage": 1.86,
            "avg_execution_time": 0.23,
            "max_execution_time": 12.5,
            "queries_per_second": 45.2,
            "trend": "improving"  # improving, stable, worsening
        }
