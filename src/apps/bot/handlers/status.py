"""
Status command handler.
"""

import typing

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from telegram import Update
from telegram import User

from apps.bot.tasks import send_daily_report
from infrastructure.bot.container import BotContainer
from infrastructure.bot.decorators import authorized
from infrastructure.bot.permissions import HAS_MOS_RU_ACCOUNT
from infrastructure.bot.permissions import IS_APPROVED
from infrastructure.bot.templates import TelegramTemplate
from utils.lang import _
from utils.telegram.context import CustomContext
from utils.telegram.response import send_response


@inject
async def status_no_account_fallback(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    user = typing.cast(User, update.effective_user)
    text = _("You have no mos.ru account. Apply account using /login command.")
    message = telegram_template.render_error(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        message,
    )


@authorized(IS_APPROVED)
@authorized(HAS_MOS_RU_ACCOUNT, status_no_account_fallback)
@inject
async def status(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    """
    Send a daily report.
    """
    user = typing.cast(User, update.effective_user)
    text = _("Getting daily report...")
    text = telegram_template.inline(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        text,
    )

    send_daily_report.delay(tg_id=user.id)
