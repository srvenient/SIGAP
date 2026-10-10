from uuid import UUID

from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: UUID
    aud: str
    jti: str
    exp: int
    iat: int