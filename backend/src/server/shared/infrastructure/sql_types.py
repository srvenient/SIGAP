from enum import Enum

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


class EnumStr(TypeDecorator):
    """Guarda un Enum de Python como texto, para no crear un tipo ENUM nativo por cada catálogo."""

    impl = String
    cache_ok = True

    def __init__(self, enum_cls: type[Enum], length: int = 40):
        super().__init__(length)
        self.enum_cls = enum_cls

    def process_bind_param(self, value, dialect):
        return None if value is None else self.enum_cls(value).value

    def process_result_value(self, value, dialect):
        return None if value is None else self.enum_cls(value)
