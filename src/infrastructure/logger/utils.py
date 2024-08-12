from infrastructure.logger.config import LoggerSettings
from utils.config import RunLevelEnum
from utils.logger import LokiConfig


def setup_loki_config(run_level: RunLevelEnum) -> LokiConfig | None:
    if run_level is not RunLevelEnum.PRODUCTION:
        return None

    logger_settings = LoggerSettings()
    loki_config = LokiConfig(
        url=logger_settings.loki_url,
        user=logger_settings.loki_user,
        password=logger_settings.loki_password.get_secret_value(),
    )
    return loki_config
