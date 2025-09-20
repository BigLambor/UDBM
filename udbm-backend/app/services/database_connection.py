"""
数据库连接服务
提供数据库连接测试和管理功能
"""
import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import psycopg2
from psycopg2 import OperationalError, DatabaseError


class DatabaseType(Enum):
    """数据库类型枚举"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    OCEANBASE = "oceanbase"


@dataclass
class ConnectionResult:
    """连接测试结果"""
    success: bool
    message: str
    response_time: float
    error_details: Optional[str] = None
    database_info: Optional[Dict[str, Any]] = None


class DatabaseConnectionService:
    """数据库连接服务类"""

    @staticmethod
    async def test_postgresql_connection(
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        timeout: int = 30
    ) -> ConnectionResult:
        """
        测试PostgreSQL数据库连接

        Args:
            host: 数据库主机
            port: 数据库端口
            database: 数据库名
            username: 用户名
            password: 密码
            timeout: 连接超时时间(秒)

        Returns:
            ConnectionResult: 连接测试结果
        """
        start_time = time.time()

        try:
            # 构建连接字符串
            conn_string = f"host={host} port={port} dbname={database} user={username} password={password} connect_timeout={timeout}"

            # 在线程池中执行同步数据库操作
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                DatabaseConnectionService._test_postgresql_sync,
                conn_string
            )

            response_time = time.time() - start_time
            return ConnectionResult(
                success=True,
                message="连接成功",
                response_time=response_time,
                database_info=result
            )

        except OperationalError as e:
            response_time = time.time() - start_time
            return ConnectionResult(
                success=False,
                message="连接失败",
                response_time=response_time,
                error_details=f"OperationalError: {str(e)}"
            )
        except DatabaseError as e:
            response_time = time.time() - start_time
            return ConnectionResult(
                success=False,
                message="数据库错误",
                response_time=response_time,
                error_details=f"DatabaseError: {str(e)}"
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ConnectionResult(
                success=False,
                message="未知错误",
                response_time=response_time,
                error_details=f"Exception: {str(e)}"
            )

    @staticmethod
    def _test_postgresql_sync(conn_string: str) -> Dict[str, Any]:
        """
        同步PostgreSQL连接测试
        """
        conn = None
        try:
            # 建立连接
            conn = psycopg2.connect(conn_string)

            # 执行测试查询
            with conn.cursor() as cursor:
                # 获取数据库版本
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]

                # 获取数据库大小
                cursor.execute("SELECT pg_database_size(current_database())")
                db_size = cursor.fetchone()[0]

                # 获取活跃连接数
                cursor.execute("""
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
                active_connections = cursor.fetchone()[0]

                # 获取表数量
                cursor.execute("""
                    SELECT count(*) as table_count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()[0]

            return {
                "version": version,
                "database_size": db_size,
                "active_connections": active_connections,
                "table_count": table_count,
                "server_encoding": conn.encoding if conn else "unknown"
            }

        finally:
            if conn:
                conn.close()

    @staticmethod
    async def test_mysql_connection(
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        timeout: int = 30
    ) -> ConnectionResult:
        """
        测试MySQL数据库连接
        """
        start_time = time.time()

        try:
            import pymysql
            
            # 在线程池中执行同步连接测试
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                DatabaseConnectionService._test_mysql_sync,
                f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}",
                timeout
            )
            
            response_time = time.time() - start_time
            
            return ConnectionResult(
                success=True,
                message="MySQL连接成功",
                response_time=response_time,
                database_info=result
            )

        except ImportError:
            response_time = time.time() - start_time
            return ConnectionResult(
                success=False,
                message="MySQL连接失败",
                response_time=response_time,
                error_details="pymysql库未安装，请运行: pip install pymysql"
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ConnectionResult(
                success=False,
                message="MySQL连接失败",
                response_time=response_time,
                error_details=str(e)
            )

    @staticmethod
    def _test_mysql_sync(conn_string: str, timeout: int = 30) -> Dict[str, Any]:
        """
        同步测试MySQL连接并获取数据库信息
        """
        import pymysql
        from urllib.parse import urlparse
        
        # 解析连接字符串
        parsed = urlparse(conn_string)
        
        conn = None
        try:
            conn = pymysql.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                database=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password,
                connect_timeout=timeout,
                charset='utf8mb4'
            )
            
            with conn.cursor() as cursor:
                # 获取MySQL版本
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                
                # 获取数据库大小
                cursor.execute("""
                    SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as db_size_mb
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, (parsed.path.lstrip('/'),))
                db_size_result = cursor.fetchone()
                db_size = db_size_result[0] if db_size_result and db_size_result[0] else 0
                
                # 获取活动连接数
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                active_connections_result = cursor.fetchone()
                active_connections = int(active_connections_result[1]) if active_connections_result else 0
                
                # 获取表数量
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, (parsed.path.lstrip('/'),))
                table_count = cursor.fetchone()[0]
                
                # 获取字符集
                cursor.execute("SHOW VARIABLES LIKE 'character_set_database'")
                charset_result = cursor.fetchone()
                charset = charset_result[1] if charset_result else "unknown"

            return {
                "version": version,
                "database_size": f"{db_size} MB",
                "active_connections": active_connections,
                "table_count": table_count,
                "charset": charset
            }

        finally:
            if conn:
                conn.close()

    @staticmethod
    async def test_connection(
        db_type: str,
        host: str,
        port: int,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ) -> ConnectionResult:
        """
        通用数据库连接测试方法

        Args:
            db_type: 数据库类型 ('postgresql', 'mysql', 'mongodb', 'redis', 'oceanbase')
            host: 主机地址
            port: 端口号
            database: 数据库名
            username: 用户名
            password: 密码
            timeout: 超时时间

        Returns:
            ConnectionResult: 连接测试结果
        """
        try:
            db_type_enum = DatabaseType(db_type.lower())
        except ValueError:
            return ConnectionResult(
                success=False,
                message="不支持的数据库类型",
                response_time=0.0,
                error_details=f"不支持的数据库类型: {db_type}"
            )

        if db_type_enum == DatabaseType.POSTGRESQL:
            return await DatabaseConnectionService.test_postgresql_connection(
                host=host,
                port=port,
                database=database or "postgres",
                username=username or "postgres",
                password=password or "",
                timeout=timeout
            )
        elif db_type_enum == DatabaseType.MYSQL:
            return await DatabaseConnectionService.test_mysql_connection(
                host=host,
                port=port,
                database=database or "",
                username=username or "",
                password=password or "",
                timeout=timeout
            )
        elif db_type_enum == DatabaseType.OCEANBASE:
            # OceanBase MySQL模式连接复用MySQL测试
            return await DatabaseConnectionService.test_mysql_connection(
                host=host,
                port=port or 2881,
                database=database or "",
                username=username or "",
                password=password or "",
                timeout=timeout
            )
        else:
            return ConnectionResult(
                success=False,
                message="数据库类型暂未实现",
                response_time=0.0,
                error_details=f"数据库类型 {db_type} 暂未实现连接测试"
            )
