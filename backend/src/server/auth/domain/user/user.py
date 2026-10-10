from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Relationship, SQLModel, Field

from src.server.shared.infrastructure.providers.system_clock import get_localized_now

if TYPE_CHECKING:
    from src.server.auth.domain.role.role import Role


class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=20, nullable=False)

    is_active: bool = Field(default=True, nullable=False)


class UserCreate(UserBase):
    role_id: UUID = Field(default=None, nullable=False)

    password: str = Field(min_length=8, max_length=40)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    role_id: Optional[UUID] = Field(
        default=None,
        foreign_key="roles.id",
        nullable=True
    )

    hashed_password: str = Field(nullable=False)

    # Bloqueo por intentos fallidos
    failed_login_attempts: int = Field(
        default=0, nullable=False,
        sa_column_kwargs={"server_default": "0"},
    )
    locked_until: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )

    last_login: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )

    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=get_localized_now,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_localized_now},
    )

    role: Optional["Role"] = Relationship(back_populates="users")


class UserPublic(UserBase):
    id: UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
