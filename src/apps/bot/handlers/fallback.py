import typing

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from telegram import Update
from telegram import User

from infrastructure.bot.container import BotContainer
from infrastructure.bot.templates import TelegramTemplate
from utils.lang import _
from utils.telegram.context import CustomContext
from utils.telegram.response import send_response


@inject
async def fallback(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    user = typing.cast(User, update.effective_user)
    text = _("Ops! I don't know what I can do.")
    text = telegram_template.render_error(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        text,
    )
