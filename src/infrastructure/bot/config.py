import hashlib
import hmac
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from infrastructure.config import BASE_DIR
from infrastructure.config import BASE_INFRA_BOT_DIR
from utils.config import RunLevelBaseConfigMixin


class TelegramBotSettings(RunLevelBaseConfigMixin, BaseSettings):
    token: SecretStr
    template_dir: Path = BASE_INFRA_BOT_DIR / "templates"
    babel_domain: str = "messages"
    babel_locale_dir: Path = BASE_DIR / "locale"
    persistence_db: int = 3

    timeout: int = 30
    read_timeout: int = 30
    write_timeout: int = 30
    connect_timeout: int = 30
    pool_timeout: int = 30

    @property
    def secret_key(self):
        base = "WebAppData".encode("utf-8")
        token = self.token.get_secret_value().encode("utf-8")
        return hmac.new(token, base, digestmod=hashlib.sha256).hexdigest()

    model_config = SettingsConfigDict(
        env_prefix="telegram_bot_",
        env_file=(".env", ".env.local"),
        extra="allow",
    )
