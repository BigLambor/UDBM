"""
核心配置管理
"""
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    """
    # 项目基本信息
    PROJECT_NAME: str = "UDBM - 统一数据库管理平台"
    API_V1_STR: str = "/api/v1"

    # 服务器配置
    SERVER_NAME: str = "UDBM"
    SERVER_HOST: AnyHttpUrl = "http://localhost"

    # 后端CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React开发服务器
        "http://localhost:8080",  # Vue开发服务器
        "http://localhost:5173",  # Vite开发服务器
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[str, List[str]]
    ) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # 数据库配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "udbm_user"
    POSTGRES_PASSWORD: str = "udbm_password"
    POSTGRES_DB: str = "udbm_db"
    POSTGRES_PORT: int = 5432

    @property
    def get_database_uri(self) -> str:
        """获取数据库连接URI，优先使用PostgreSQL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # 数据库连接池配置
    SQLALCHEMY_POOL_SIZE: int = 5  # 减少基础连接池大小
    SQLALCHEMY_MAX_OVERFLOW: int = 10  # 减少最大溢出连接数
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    SQLALCHEMY_POOL_RECYCLE: int = 1800

    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_PATH: str = "/tmp/udbm/uploads"

    # 监控配置
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }


# 创建全局配置实例
settings = Settings()
