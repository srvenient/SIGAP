import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from src.server.shared.infrastructure.providers.system_clock import get_localized_now


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    family_id: uuid.UUID = Field(index=True, nullable=False)
    token_hash: str = Field(unique=True, index=True, nullable=False, max_length=64)

    expires_at: datetime = Field(nullable=False, sa_type=DateTime(timezone=True))
    absolute_expires_at: datetime = Field(nullable=False, sa_type=DateTime(timezone=True))

    revoked_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True)
    )