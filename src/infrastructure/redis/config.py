"""
Redis configuration.
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from utils.config import RunLevelBaseConfigMixin


class RedisSettings(RunLevelBaseConfigMixin, BaseSettings):
    host: str = "localhost"
    port: int = 6379
    db: int = 0

    @property
    def url(self):
        return f"redis://{self.host}:{self.port}/{self.db}"

    model_config = SettingsConfigDict(
        env_prefix="redis_",
        env_file=(".env", ".env.local"),
        extra="allow",
    )
