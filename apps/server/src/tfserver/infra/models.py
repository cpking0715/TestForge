"""表模型（infra 层）：RBAC 核心。

字段语义对标「用户/角色/菜单」三件套，命名自研。
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tfserver.infra.db import Base

# 关联表：用户-角色 / 角色-菜单
user_role = Table(
    "sys_user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True),
)
role_menu = Table(
    "sys_role_menu",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True),
    Column("menu_id", Integer, ForeignKey("sys_menu.id", ondelete="CASCADE"), primary_key=True),
)


class SystemUser(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(64), default="")
    email: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[bool] = mapped_column(Boolean, default=True)  # True=启用
    is_super: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=func.now())

    roles: Mapped[list["Role"]] = relationship(secondary=user_role, back_populates="users", lazy="selectin")

    @property
    def role_codes(self) -> list[str]:
        return [r.code for r in self.roles]


class Role(Base):
    __tablename__ = "sys_role"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    remark: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    users: Mapped[list[SystemUser]] = relationship(secondary=user_role, back_populates="roles")
    menus: Mapped[list["Menu"]] = relationship(secondary=role_menu, lazy="selectin")


class Menu(Base):
    __tablename__ = "sys_menu"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_menu.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(64))
    # 类型：dir=目录 / page=页面 / button=按钮
    type: Mapped[str] = mapped_column(String(16), default="page")
    path: Mapped[str] = mapped_column(String(128), default="")
    permission: Mapped[str] = mapped_column(String(128), default="")  # 如 system:user:list
    icon: Mapped[str] = mapped_column(String(64), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)

    children: Mapped[list["Menu"]] = relationship(lazy="selectin")
