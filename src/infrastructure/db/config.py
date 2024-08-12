"""
Database service configuration.
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from utils.config import RunLevelBaseConfigMixin


class DatabaseSettings(RunLevelBaseConfigMixin, BaseSettings):
    host: str
    user: str
    password: str
    name: str
    debug: bool = False

    @property
    def url(self):
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}/{self.name}"

    model_config = SettingsConfigDict(
        env_prefix="db_",
        env_file=(".env", ".env.local"),
        extra="allow",
    )
