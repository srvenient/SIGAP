from core import security
from src.server.auth.domain.exceptions import UsernameAlreadyExists, RoleNotFound
from src.server.auth.domain.user.user import User, UserCreate
from src.server.auth.domain.user.user_repository import UserRepository
from src.server.auth.domain.role.role_repository import RoleRepository


class UserService:
    def __init__(self, user_repository: UserRepository, role_repository: RoleRepository):
        self.user_repository = user_repository
        self.role_repository = role_repository

    async def create_user(self, user_create: UserCreate):
        if await self.user_repository.find_by_username(user_create.username):
            raise UsernameAlreadyExists

        if await self.role_repository.find_by_id(user_create.role_id):
            raise RoleNotFound

        user = User(
            username=user_create.username,
            hashed_password=security.get_password_hash(user_create.password),
            role_id=user_create.role_id,
            is_active=user_create.is_active
        )

        return await self.user_repository.save(user)
