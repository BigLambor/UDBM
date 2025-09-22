"""
数据库实例管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.models.database import DatabaseInstance
from app.services.database_connection import DatabaseConnectionService
from app.schemas.database import (
    DatabaseInstanceResponse,
    DatabaseInstanceCreate,
    DatabaseInstanceUpdate,
    DatabaseTestConnectionRequest,
    DatabaseTestConnectionResponse
)

router = APIRouter()


@router.get("/", response_model=List[DatabaseInstanceResponse])
async def list_databases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """获取数据库实例列表"""
    try:
        result = await db.execute(
            text("SELECT * FROM database_instances ORDER BY created_at DESC LIMIT :limit OFFSET :skip"),
            {"limit": limit, "skip": skip}
        )
        databases = result.fetchall()

        # 获取数据库类型映射
        type_result = await db.execute(text("SELECT id, name FROM database_types"))
        type_mapping = {row.id: row.name for row in type_result.fetchall()}

        # 转换为响应格式
        response = []
        for db_row in databases:
            response.append({
                "id": db_row.id,
                "name": db_row.name,
                "type_id": db_row.type_id,
                "type": type_mapping.get(db_row.type_id, "unknown"),
                "host": db_row.host,
                "port": db_row.port,
                "database_name": db_row.database_name,
                "username": db_row.username,
                "status": db_row.status,
                "environment": db_row.environment,
                "health_status": db_row.health_status,
                "last_health_check": db_row.last_health_check.isoformat() if db_row.last_health_check else None,
                "created_at": db_row.created_at.isoformat() if db_row.created_at else None,
                "updated_at": db_row.updated_at.isoformat() if db_row.updated_at else None
            })

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库列表失败: {str(e)}")


@router.post("/", response_model=DatabaseInstanceResponse)
async def create_database(
    database: DatabaseInstanceCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建数据库实例"""
    try:
        # 插入新数据库实例
        result = await db.execute(
            text("""
            INSERT INTO database_instances
            (name, type_id, host, port, database_name, username, password_encrypted,
             environment, status, health_status)
            VALUES (:name, :type_id, :host, :port, :database_name, :username, :password_encrypted,
                    :environment, :status, :health_status)
            RETURNING *
            """),
            {
                "name": database.name,
                "type_id": database.type_id,
                "host": database.host,
                "port": database.port,
                "database_name": database.database_name,
                "username": database.username,
                "password_encrypted": database.password_encrypted,
                "environment": database.environment,
                "status": database.status,
                "health_status": database.health_status
            }
        )

        db_row = result.fetchone()
        await db.commit()

        # 获取数据库类型名称
        type_result = await db.execute(
            text("SELECT name FROM database_types WHERE id = :type_id"),
            {"type_id": db_row.type_id}
        )
        type_row = type_result.fetchone()
        type_name = type_row.name if type_row else "unknown"

        return {
            "id": db_row.id,
            "name": db_row.name,
            "type_id": db_row.type_id,
            "type": type_name,
            "host": db_row.host,
            "port": db_row.port,
            "database_name": db_row.database_name,
            "username": db_row.username,
            "status": db_row.status,
            "environment": db_row.environment,
            "health_status": db_row.health_status,
            "last_health_check": db_row.last_health_check.isoformat() if db_row.last_health_check else None,
            "created_at": db_row.created_at.isoformat() if db_row.created_at else None,
            "updated_at": db_row.updated_at.isoformat() if db_row.updated_at else None
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建数据库实例失败: {str(e)}")


@router.get("/{database_id}", response_model=DatabaseInstanceResponse)
async def get_database(
    database_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取数据库实例详情"""
    try:
        result = await db.execute(
            text("SELECT * FROM database_instances WHERE id = :id"),
            {"id": database_id}
        )
        db_row = result.fetchone()

        if not db_row:
            raise HTTPException(status_code=404, detail="数据库实例不存在")

        # 获取数据库类型名称
        type_result = await db.execute(
            text("SELECT name FROM database_types WHERE id = :type_id"),
            {"type_id": db_row.type_id}
        )
        type_row = type_result.fetchone()
        type_name = type_row.name if type_row else "unknown"

        return {
            "id": db_row.id,
            "name": db_row.name,
            "type_id": db_row.type_id,
            "type": type_name,
            "host": db_row.host,
            "port": db_row.port,
            "database_name": db_row.database_name,
            "username": db_row.username,
            "status": db_row.status,
            "environment": db_row.environment,
            "health_status": db_row.health_status,
            "last_health_check": db_row.last_health_check.isoformat() if db_row.last_health_check else None,
            "created_at": db_row.created_at.isoformat() if db_row.created_at else None,
            "updated_at": db_row.updated_at.isoformat() if db_row.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库详情失败: {str(e)}")


@router.put("/{database_id}", response_model=DatabaseInstanceResponse)
async def update_database(
    database_id: int,
    database: DatabaseInstanceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新数据库实例"""
    try:
        # 构建更新字段
        update_fields = {}
        if database.name is not None:
            update_fields["name"] = database.name
        if database.host is not None:
            update_fields["host"] = database.host
        if database.port is not None:
            update_fields["port"] = database.port
        if database.database_name is not None:
            update_fields["database_name"] = database.database_name
        if database.username is not None:
            update_fields["username"] = database.username
        if database.password_encrypted is not None:
            update_fields["password_encrypted"] = database.password_encrypted
        if database.status is not None:
            update_fields["status"] = database.status
        if database.environment is not None:
            update_fields["environment"] = database.environment
        if database.health_status is not None:
            update_fields["health_status"] = database.health_status

        if not update_fields:
            raise HTTPException(status_code=400, detail="没有提供需要更新的字段")

        # 构建SET子句
        set_clause = ", ".join([f"{k} = :{k}" for k in update_fields.keys()])
        update_fields["id"] = database_id

        # 执行更新
        result = await db.execute(
            text(f"""
            UPDATE udbm.database_instances
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            RETURNING *
            """),
            update_fields
        )

        db_row = result.fetchone()
        if not db_row:
            raise HTTPException(status_code=404, detail="数据库实例不存在")

        await db.commit()

        # 获取数据库类型名称
        type_result = await db.execute(
            text("SELECT name FROM database_types WHERE id = :type_id"),
            {"type_id": db_row.type_id}
        )
        type_row = type_result.fetchone()
        type_name = type_row.name if type_row else "unknown"

        return {
            "id": db_row.id,
            "name": db_row.name,
            "type_id": db_row.type_id,
            "type": type_name,
            "host": db_row.host,
            "port": db_row.port,
            "database_name": db_row.database_name,
            "username": db_row.username,
            "status": db_row.status,
            "environment": db_row.environment,
            "health_status": db_row.health_status,
            "last_health_check": db_row.last_health_check.isoformat() if db_row.last_health_check else None,
            "created_at": db_row.created_at.isoformat() if db_row.created_at else None,
            "updated_at": db_row.updated_at.isoformat() if db_row.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新数据库实例失败: {str(e)}")


@router.delete("/{database_id}")
async def delete_database(
    database_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除数据库实例"""
    try:
        result = await db.execute(
            text("DELETE FROM database_instances WHERE id = :id RETURNING id"),
            {"id": database_id}
        )

        if not result.fetchone():
            raise HTTPException(status_code=404, detail="数据库实例不存在")

        await db.commit()
        return {"message": "数据库实例删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除数据库实例失败: {str(e)}")


@router.post("/{database_id}/test-connection", response_model=DatabaseTestConnectionResponse)
async def test_database_connection(
    database_id: int,
    db: AsyncSession = Depends(get_db)
):
    """测试数据库连接"""
    try:
        # 获取数据库实例信息
        result = await db.execute(
            text("SELECT * FROM database_instances WHERE id = :id"),
            {"id": database_id}
        )
        db_instance = result.fetchone()

        if not db_instance:
            raise HTTPException(status_code=404, detail="数据库实例不存在")

        # 获取数据库类型信息
        type_result = await db.execute(
            text("SELECT * FROM database_types WHERE id = :type_id"),
            {"type_id": db_instance.type_id}
        )
        db_type = type_result.fetchone()

        if not db_type:
            raise HTTPException(status_code=404, detail="数据库类型不存在")

        # 调用连接测试服务
        connection_result = await DatabaseConnectionService.test_connection(
            db_type=db_type.name,
            host=db_instance.host,
            port=db_instance.port,
            database=db_instance.database_name,
            username=db_instance.username,
            password=db_instance.password_encrypted  # 注意：实际应该解密
        )

        return {
            "database_id": database_id,
            "success": connection_result.success,
            "message": connection_result.message,
            "response_time": connection_result.response_time,
            "error_details": connection_result.error_details,
            "database_info": connection_result.database_info
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接测试失败: {str(e)}")
