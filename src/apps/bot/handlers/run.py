import typing

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from telegram import Update
from telegram import User

from apps.ag.tasks import pass_novelties
from apps.ag.tasks import pass_novelty
from apps.ag.tasks import pass_poll
from apps.ag.tasks import pass_polls
from infrastructure.bot.container import BotContainer
from infrastructure.bot.decorators import authorized
from infrastructure.bot.permissions import HAS_MOS_RU_ACCOUNT
from infrastructure.bot.permissions import IS_APPROVED
from infrastructure.bot.templates import TelegramTemplate
from utils.lang import _
from utils.telegram.context import CustomContext
from utils.telegram.response import send_response


@inject
async def run_no_account_fallback(
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
@authorized(HAS_MOS_RU_ACCOUNT, run_no_account_fallback)
async def run_poll(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    user = typing.cast(User, update.effective_user)
    tg_id = user.id
    poll_id = context.kwargs["poll_id"]
    pass_poll.delay(tg_id=tg_id, poll_id=poll_id)

    text = _("Poll %(id)s has begun.")
    text = telegram_template.inline(
        text,
        user.language_code,
        id=poll_id,
    )

    await send_response(
        update,
        context,
        text,
    )


@authorized(IS_APPROVED)
@authorized(HAS_MOS_RU_ACCOUNT, run_no_account_fallback)
async def run_novelty(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    user = typing.cast(User, update.effective_user)
    tg_id = user.id
    novelty_id = context.kwargs["novelty_id"]
    pass_novelty.delay(tg_id=tg_id, novelty_id=novelty_id)

    text = _("Novelty %(id)s has begun.")
    text = telegram_template.inline(
        text,
        user.language_code,
        id=novelty_id,
    )

    await send_response(
        update,
        context,
        text,
    )


@authorized(IS_APPROVED)
@authorized(HAS_MOS_RU_ACCOUNT, run_no_account_fallback)
async def run_all(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    user = typing.cast(User, update.effective_user)
    tg_id = user.id
    pass_polls.delay(tg_id=tg_id)
    pass_novelties.delay(tg_id=tg_id)

    text = _("All tasks has begun.")
    text = telegram_template.inline(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        text,
    )


@authorized(IS_APPROVED)
@authorized(HAS_MOS_RU_ACCOUNT, run_no_account_fallback)
async def run_novelty_all(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    user = typing.cast(User, update.effective_user)
    tg_id = user.id
    pass_novelties.delay(tg_id=tg_id)

    text = _("All novelties tasks has begun.")
    text = telegram_template.inline(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        text,
    )


@authorized(IS_APPROVED)
@authorized(HAS_MOS_RU_ACCOUNT, run_no_account_fallback)
async def run_poll_all(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> None:
    user = typing.cast(User, update.effective_user)
    tg_id = user.id
    pass_polls.delay(tg_id=tg_id)

    text = _("All polls tasks has begun.")
    text = telegram_template.inline(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        text,
    )
