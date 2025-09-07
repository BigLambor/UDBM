"""
数据库适配层 - Provider 注册与工厂
"""
from typing import Dict, Type
from sqlalchemy.orm import Session

from app.models.database import DatabaseInstance, DatabaseType
from app.services.db_providers.postgres import PostgresProvider


_type_to_provider: Dict[str, Type] = {
    "postgresql": PostgresProvider,
}


def get_database_type_name(session: Session, database_id: int) -> str:
    row = (
        session.query(DatabaseInstance, DatabaseType)
        .join(DatabaseType, DatabaseType.id == DatabaseInstance.type_id)
        .filter(DatabaseInstance.id == database_id)
        .first()
    )
    return row[1].name if row else "postgresql"


def get_provider(session: Session, database_id: int):
    name = get_database_type_name(session, database_id)
    provider_cls = _type_to_provider.get(name, PostgresProvider)
    return provider_cls(session)

