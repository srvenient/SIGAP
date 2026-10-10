from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

_password_hash = PasswordHash((Argon2Hasher(),))
DUMMY_HASHED_PASSWORD = _password_hash.hash("dummy_password")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return _password_hash.hash(password)
