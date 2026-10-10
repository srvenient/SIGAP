import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Relationship, SQLModel, Field

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

    last_login: Optional[datetime.datetime] = Field(default=None)

    created_at: datetime.datetime = Field(
        nullable=False,
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = Field(
        nullable=False,
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column_kwargs={"onupdate": datetime.datetime.now(datetime.timezone.utc)}
    )

    role: Optional["Role"] = Relationship(back_populates="users")


class UserPublic(UserBase):
    id: UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
