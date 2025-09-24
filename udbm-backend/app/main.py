"""
UDBM - 统一数据库管理平台
主应用入口文件
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 初始化数据库实例
    try:
        from app.db.init_database_instances import initialize_database_instances
        await initialize_database_instances()
    except Exception as e:
        print(f"警告：数据库实例初始化失败: {e}")

    yield

    # 关闭时：清理资源
    await engine.dispose()


def create_application() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="统一数据库管理平台API",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        debug=True,  # 启用调试模式
    )

    # 设置CORS - 支持局域网访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000", 
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
            # 支持局域网访问 - 允许所有192.168.x.x和10.x.x.x网段
            "http://192.168.0.0/16",
            "http://10.0.0.0/8",
            "http://172.16.0.0/12",
            # 支持所有来源（开发环境）
            "*"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 包含API路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/health")
    async def health_check():
        """健康检查接口"""
        return {"status": "healthy", "message": "UDBM API is running"}

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
