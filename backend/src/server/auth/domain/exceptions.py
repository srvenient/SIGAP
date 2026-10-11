class AuthError(Exception): ...


class InvalidCredentials(AuthError): ...


class InactiveUser(AuthError): ...


class InvalidToken(AuthError): ...


class InvalidPassword(AuthError): ...  # contraseña actual incorrecta


class SamePassword(AuthError): ...  # la nueva es igual a la actual


class AccountLocked(AuthError):
    def __init__(self, retry_after: int):
        super().__init__(f"Account locked for {retry_after}s")
        self.retry_after = retry_after


class UserError(Exception): ...


class UsernameAlreadyExists(UserError): ...


class UserNotFound(UserError): ...


class RoleNotFound(UserError): ...


class CannotModifySelf(UserError): ...
