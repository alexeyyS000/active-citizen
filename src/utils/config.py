"""
Common configuration.
"""

from enum import Enum

from pydantic_settings import BaseSettings


class RunLevelEnum(Enum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"


class RunLevelBaseConfigMixin(BaseSettings):
    run_level: RunLevelEnum = RunLevelEnum.DEVELOPMENT
