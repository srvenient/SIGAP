import datetime
import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Relationship, SQLModel, Field

if TYPE_CHECKING:
    from server.auth.domain.role.role import Role


class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=20, nullable=False)

    is_active: bool = Field(default=True, nullable=False)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username")
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    role_id: Optional[uuid.UUID] = Field(
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
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
