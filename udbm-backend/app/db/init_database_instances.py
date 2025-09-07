"""
数据库实例初始化脚本
自动将PostgreSQL实例信息插入到数据库实例管理中
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import Optional

from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseInstanceInitializer:
    """数据库实例初始化器"""

    def __init__(self):
        self.engine = create_async_engine(
            settings.get_database_uri,
            pool_size=settings.SQLALCHEMY_POOL_SIZE,
            max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
            pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
            pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
            echo=False,
        )

        self.async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_postgres_type_id(self, session: AsyncSession) -> Optional[int]:
        """获取PostgreSQL数据库类型的ID"""
        try:
            result = await session.execute(
                text("SELECT id FROM udbm.database_types WHERE name = 'postgresql' AND is_active = true")
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"获取PostgreSQL类型ID失败: {e}")
            return None

    async def check_instance_exists(self, session: AsyncSession, type_id: int) -> bool:
        """检查PostgreSQL实例是否已存在"""
        try:
            result = await session.execute(
                text("""
                    SELECT COUNT(*) FROM udbm.database_instances
                    WHERE type_id = :type_id AND host = 'localhost' AND port = 5432
                """),
                {"type_id": type_id}
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            logger.error(f"检查实例存在性失败: {e}")
            return False

    async def create_postgres_instance(self, session: AsyncSession, type_id: int):
        """创建PostgreSQL实例记录"""
        try:
            # 插入PostgreSQL实例
            await session.execute(
                text("""
                    INSERT INTO udbm.database_instances
                    (name, type_id, host, port, database_name, username, password_encrypted,
                     environment, status, health_status, ssl_enabled, tags)
                    VALUES
                    (:name, :type_id, :host, :port, :database_name, :username, :password,
                     :environment, :status, :health_status, :ssl_enabled, :tags)
                """),
                {
                    "name": "UDBM PostgreSQL Database",
                    "type_id": type_id,
                    "host": "localhost",  # 从宿主机连接
                    "port": 5432,
                    "database_name": "udbm_db",
                    "username": "udbm_user",
                    "password": "udbm_password",  # 注意：生产环境应该加密存储
                    "environment": "development",
                    "status": "active",
                    "health_status": "unknown",
                    "ssl_enabled": False,
                    "tags": '{"auto_created": true, "purpose": "system_database"}'
                }
            )

            logger.info("PostgreSQL实例创建成功")

        except Exception as e:
            logger.error(f"创建PostgreSQL实例失败: {e}")
            raise

    async def initialize_postgres_instance(self):
        """初始化PostgreSQL实例"""
        logger.info("开始初始化PostgreSQL实例...")

        async with self.async_session() as session:
            try:
                # 1. 获取PostgreSQL类型ID
                type_id = await self.get_postgres_type_id(session)
                if not type_id:
                    logger.error("PostgreSQL数据库类型不存在，请先初始化数据库类型")
                    return False

                logger.info(f"找到PostgreSQL类型ID: {type_id}")

                # 2. 检查实例是否已存在
                exists = await self.check_instance_exists(session, type_id)
                if exists:
                    logger.info("PostgreSQL实例已存在，跳过创建")
                    return True

                # 3. 创建PostgreSQL实例
                await self.create_postgres_instance(session, type_id)

                # 4. 提交事务
                await session.commit()

                logger.info("PostgreSQL实例初始化完成")
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"PostgreSQL实例初始化失败: {e}")
                return False

    async def close(self):
        """关闭数据库连接"""
        await self.engine.dispose()


async def initialize_database_instances():
    """初始化数据库实例的主函数"""
    initializer = DatabaseInstanceInitializer()

    try:
        success = await initializer.initialize_postgres_instance()
        if success:
            logger.info("✅ 数据库实例初始化成功")
        else:
            logger.error("❌ 数据库实例初始化失败")
    finally:
        await initializer.close()


if __name__ == "__main__":
    # 直接运行时的入口
    asyncio.run(initialize_database_instances())
