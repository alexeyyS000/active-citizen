"""
AG bot configuration.
"""

from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class AgSettings(BaseSettings):
    headless: bool = False
    state_path: Path = Path("state.json")

    model_config = SettingsConfigDict(
        env_prefix="ag_",
        env_file=(".env", ".env.local"),
        extra="allow",
    )
