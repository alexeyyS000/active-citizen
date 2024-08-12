"""
Worker service configuration.
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from utils.config import RunLevelBaseConfigMixin


class WorkerSettings(RunLevelBaseConfigMixin, BaseSettings):
    celery_broker_url: str
    celery_result_backend: str

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        extra="allow",
    )
