from pathlib import Path
from typing import Literal, Annotated, Any

from pydantic import PostgresDsn, computed_field, Field, BeforeValidator, AnyUrl, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    DEVICE_TYPE: Literal["cpu", "cu130"]

    DEBUG: bool = False

    LOG_LEVEL: Literal["debug", "info", "warn", "error"]

    PROJECT_NAME: str
    PROJECT_VERSION: str


settings = Settings()  # type: ignore
