"""
用户模型定义
"""
from sqlalchemy import String, Boolean, Integer, TIMESTAMP, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.db.base import Base, TimestampMixin, UserMixin


class User(Base, TimestampMixin, UserMixin):
    """
    用户表模型
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50),  nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100),  nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=True)

    # 关联关系
    # created_databases = relationship(
    #     "DatabaseInstance",
    #     back_populates="creator",
    #     foreign_keys="DatabaseInstance.created_by"
    # )
    





class Role(Base, TimestampMixin):
    """
    角色表模型
    """
    __tablename__ = "roles"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50),  nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    permissions: Mapped[str] = mapped_column(String, default='{}', nullable=False)  # JSON字符串
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class UserRole(Base, TimestampMixin):
    """
    用户角色关联表
    """
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    granted_by: Mapped[int] = mapped_column(Integer, nullable=True)
    granted_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, default=func.now())
    expires_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=True)




class Permission(Base, TimestampMixin):
    """
    权限表模型
    """
    __tablename__ = "permissions"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)




class RolePermission(Base, TimestampMixin):
    """
    角色权限关联表
    """
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "udbm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    granted_by: Mapped[int] = mapped_column(Integer, nullable=True)
    granted_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, default=func.now())


