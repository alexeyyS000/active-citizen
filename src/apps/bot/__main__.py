"""
Telegram Bot entrypoint.
"""

import structlog
from telegram import Update
from telegram import __version__ as tg_version
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import TypeHandler
from telegram.ext import filters

from apps.bot import handlers
from infrastructure.bot.config import TelegramBotSettings
from infrastructure.bot.container import BotContainer
from infrastructure.logger.utils import setup_loki_config
from infrastructure.redis.config import RedisSettings
from utils.logger import setup_logger
from utils.telegram.context import CustomContext
from utils.telegram.handlers import CommandWithArgsHandler
from utils.telegram.persistence import RedisPersistence

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {tg_version}. To view the "
        f"{tg_version} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{tg_version}/examples.html"
    )
from telegram.ext import Application
from telegram.ext import CommandHandler

# Enable logging
logger = structlog.get_logger()


def main() -> None:
    """Run the bot."""
    telegram_settings = TelegramBotSettings()
    redis_settings = RedisSettings()

    loki_config = setup_loki_config(telegram_settings.run_level)
    setup_logger(run_level=telegram_settings.run_level, loki_config=loki_config)

    context_types = ContextTypes(CustomContext)
    persistence = RedisPersistence(
        redis_settings.host,
        redis_settings.port,
        telegram_settings.persistence_db,
    )
    application = (
        Application.builder()
        .context_types(context_types)
        .persistence(persistence)
        .token(telegram_settings.token.get_secret_value())
        .build()
    )

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("status", handlers.status))
    application.add_handler(
        CommandWithArgsHandler(
            "run",
            ["poll", "<int:poll_id>"],
            handlers.run_poll,
        )
    )
    application.add_handler(
        CommandWithArgsHandler(
            "run",
            ["novelty", "<int:novelty_id>"],
            handlers.run_novelty,
        )
    )
    application.add_handler(
        CommandWithArgsHandler(
            "run",
            ["all"],
            handlers.run_all,
        )
    )
    application.add_handler(
        CommandWithArgsHandler(
            "run",
            ["poll", "all"],
            handlers.run_poll_all,
        )
    )
    application.add_handler(
        CommandWithArgsHandler(
            "run",
            ["novelty", "all"],
            handlers.run_novelty_all,
        )
    )
    application.add_handler(handlers.login_conv)
    application.add_handler(handlers.admin_conv)
    application.add_handler(handlers.schedule_conv)

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handlers.fallback,
        )
    )

    # Add audit log handler.
    application.add_handler(TypeHandler(Update, handlers.audit_log), -2)
    application.add_handler(TypeHandler(Update, handlers.get_user), -1)

    application.run_polling(
        timeout=telegram_settings.timeout,
        read_timeout=telegram_settings.read_timeout,
        write_timeout=telegram_settings.write_timeout,
        pool_timeout=telegram_settings.pool_timeout,
        connect_timeout=telegram_settings.connect_timeout,
    )


if __name__ == "__main__":
    container = BotContainer()
    container.wire(
        packages=[
            __name__,
            "apps.bot.handlers",
        ],
    )

    main()
