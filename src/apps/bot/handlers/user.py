import typing

import structlog
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from telegram import Update
from telegram import User

from core import models
from core.services.user import AsyncUserService
from infrastructure.bot.container import BotContainer
from utils.telegram.context import CustomContext

logger = structlog.get_logger()


@inject
async def get_user(
    update: Update,
    context: CustomContext,
    user_async_service: AsyncUserService = Provide[BotContainer.user_async_service],
) -> None:
    """
    Get or create user.
    """
    current_user = typing.cast(User, update.effective_user)
    user_data = typing.cast(dict, context.user_data)

    default = dict(
        tg_id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        username=current_user.username,
        language_code=current_user.language_code,
    )

    user: models.User

    user, created = await user_async_service.get_or_create(default, tg_id=current_user.id)

    if created:
        logger.info("User was created.")

    user_data["user"] = user
