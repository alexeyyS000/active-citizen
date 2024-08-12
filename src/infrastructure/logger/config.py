from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from utils.config import RunLevelBaseConfigMixin


class LoggerSettings(RunLevelBaseConfigMixin, BaseSettings):
    loki_url: str
    loki_user: str
    loki_password: SecretStr
    loki_version: str = "1"

    model_config = SettingsConfigDict(
        env_prefix="logger_",
        env_file=(".env", ".env.local"),
        extra="allow",
    )
