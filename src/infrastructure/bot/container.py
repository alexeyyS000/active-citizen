"""
Bot DI container.
"""

from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from core import dal
from core.services.user import AsyncUserService
from infrastructure.ag.config import AgSettings
from infrastructure.bot.config import TelegramBotSettings
from infrastructure.bot.templates import TelegramTemplate
from infrastructure.db.client import AsyncDatabase
from infrastructure.db.config import DatabaseSettings
from infrastructure.minio.config import MinioSettings


class BotContainer(DeclarativeContainer):
    database_config = DatabaseSettings()
    telegram_bot_config = TelegramBotSettings()
    minio_settings = MinioSettings()
    ag_settings = AgSettings()

    telegram_template = providers.Singleton(
        TelegramTemplate,
        template_dir=telegram_bot_config.template_dir,
        babel_domain=telegram_bot_config.babel_domain,
        babel_locale_dir=telegram_bot_config.babel_locale_dir,
    )
    async_db = providers.Singleton(
        AsyncDatabase,
        db_url=database_config.url,
        echo=database_config.debug,
    )
    user_async_dal = providers.Factory(
        dal.UserAsyncDAL,
        session_factory=async_db.provided.session,
    )
    mos_ru_user_async_dal = providers.Factory(
        dal.MosRuUserAsyncDAL,
        session_factory=async_db.provided.session,
    )

    schedule_async_dal = providers.Factory(
        dal.AlertScheduleAsyncDAL,
        session_factory=async_db.provided.session,
    )

    user_async_service = providers.Factory(AsyncUserService, user_async_dal, schedule_async_dal)

    task_log_async_dal = providers.Factory(
        dal.TaskLogAsyncDAL,
        session_factory=async_db.provided.session,
    )
