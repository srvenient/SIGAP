import re
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import DateTime, false
from sqlmodel import Relationship, SQLModel, Field

from src.server.auth.domain.role.role import RolePublic
from src.server.shared.infrastructure.providers.system_clock import get_localized_now

if TYPE_CHECKING:
    from src.server.auth.domain.role.role import Role


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=20, nullable=False)

    full_name: Optional[str] = Field(default=None, max_length=80)
    email: Optional[str] = Field(default=None, max_length=120)

    is_active: bool = Field(default=True, nullable=False)


class UserCreate(UserBase):
    role_id: UUID

    password: str = Field(min_length=8, max_length=40)

    @field_validator("username")
    @classmethod
    def _username_format(cls, value: str) -> str:
        # '@' queda reservado para distinguir un correo de un username en el login
        if "@" in value or any(ch.isspace() for ch in value):
            raise ValueError("El nombre de usuario no puede contener '@' ni espacios")
        return value

    @field_validator("full_name", mode="before")
    @classmethod
    def _clean_full_name(cls, value):
        if isinstance(value, str):
            value = " ".join(value.split())
        return value or None

    @field_validator("email", mode="before")
    @classmethod
    def _clean_email(cls, value):
        if not isinstance(value, str) or not value.strip():
            return None
        value = value.strip().lower()
        if not _EMAIL_RE.match(value):
            raise ValueError("Correo electrónico inválido")
        return value


class UserUpdate(SQLModel):
    role_id: UUID | None = None
    is_active: bool | None = None


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

    must_change_password: bool = Field(
        default=False, nullable=False,
        sa_column_kwargs={"server_default": false()},
    )
    password_changed_at: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )

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

    # "selectin": el rol se carga junto al usuario. El lazy-load por defecto
    # falla en sesiones async (MissingGreenlet) al acceder a user.role.
    role: Optional["Role"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @property
    def is_superuser(self) -> bool:
        from core.config import settings
        return self.username == settings.FIRST_SUPERUSER


class UserPublic(UserBase):
    id: UUID
    role_id: UUID | None = None
    role: RolePublic | None = None
    is_superuser: bool = False
    must_change_password: bool = False
    locked_until: datetime | None = None
    last_login: datetime | None = None
    created_at: datetime


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
