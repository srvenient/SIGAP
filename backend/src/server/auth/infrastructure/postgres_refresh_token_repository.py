from uuid import UUID

from sqlalchemy import delete, update
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.auth.domain.token.refresh_token import RefreshToken
from src.server.auth.domain.token.refresh_token_repository import RefreshTokenRepository


class PostgresRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, token: RefreshToken) -> RefreshToken:
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(col(RefreshToken.id) == token_id, col(RefreshToken.revoked_at).is_(None))
            .values(revoked_at=get_localized_now())
        )
        await self.session.commit()

    async def revoke_family(self, family_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(col(RefreshToken.family_id) == family_id, col(RefreshToken.revoked_at).is_(None))
            .values(revoked_at=get_localized_now())
        )
        await self.session.commit()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(col(RefreshToken.user_id) == user_id, col(RefreshToken.revoked_at).is_(None))
            .values(revoked_at=get_localized_now())
        )
        await self.session.commit()

    async def delete_expired(self) -> int:
        result = await self.session.execute(
            delete(RefreshToken).where(col(RefreshToken.expires_at) < get_localized_now())
        )
        await self.session.commit()
        return result.rowcount
