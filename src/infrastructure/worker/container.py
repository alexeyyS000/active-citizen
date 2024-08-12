"""
Worker DI container.
"""

import telebot
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from core import dal
from core.dal.files import FilesBucketClient
from infrastructure.ag.config import AgSettings
from infrastructure.ag.web.client import AgWebClient
from infrastructure.bot.client.sync import TelegramBotClient
from infrastructure.bot.config import TelegramBotSettings
from infrastructure.bot.templates import TelegramTemplate
from infrastructure.db.client.sync import Database
from infrastructure.db.config import DatabaseSettings
from infrastructure.minio.config import MinioSettings


class WorkerContainer(DeclarativeContainer):
    database_config = DatabaseSettings()
    telegram_bot_config = TelegramBotSettings()
    minio_settings = MinioSettings()
    ag_settings = AgSettings()

    files_client = providers.Factory(
        FilesBucketClient,
        url=minio_settings.url,
        access_key=minio_settings.access_key.get_secret_value(),
        secret_key=minio_settings.secret_key.get_secret_value(),
    )

    db = providers.Singleton(
        Database,
        db_url=database_config.url,
        echo=database_config.debug,
    )
    pass_log_dal = providers.Factory(dal.PassLogDAL, session_factory=db.provided.session)
    user_dal = providers.Factory(dal.UserDAL, session_factory=db.provided.session)
    mos_ru_user_dal = providers.Factory(dal.MosRuUserDAL, session_factory=db.provided.session)

    telegram_bot: telebot.TeleBot = providers.Factory(
        telebot.TeleBot,
        token=telegram_bot_config.token.get_secret_value(),
    )
    telegram_bot_client: providers.Factory[TelegramBotClient] = providers.Factory(
        TelegramBotClient,
        bot=telegram_bot,
    )
    telegram_template = providers.Singleton(
        TelegramTemplate,
        template_dir=telegram_bot_config.template_dir,
        babel_domain=telegram_bot_config.babel_domain,
        babel_locale_dir=telegram_bot_config.babel_locale_dir,
    )

    ag_web_client: providers.Factory[AgWebClient] = providers.Factory(
        AgWebClient,
        headless=ag_settings.headless,
        files_client=files_client,
    )

    schedule_sync_dal = providers.Factory(dal.AlertScheduleDAL, session_factory=db.provided.session)

    task_log_sync_dal = providers.Factory(dal.TaskLogDAL, session_factory=db.provided.session)
