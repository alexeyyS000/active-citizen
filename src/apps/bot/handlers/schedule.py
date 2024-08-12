import typing
from datetime import datetime

import structlog
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Message
from telegram import Update
from telegram import User
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler

from apps.bot.tasks import redefine_alert_task
from core import dal
from infrastructure.bot.container import BotContainer
from infrastructure.bot.decorators import authorized
from infrastructure.bot.permissions import IS_APPROVED
from infrastructure.bot.templates import TelegramTemplate
from infrastructure.db.utils.enums import AlertScheduleTypeEnum
from utils.lang import _
from utils.telegram.context import CustomContext
from utils.telegram.filters import IS_VALID_TIME_FILTER
from utils.telegram.response import send_response

logger = structlog.get_logger()


TIME, SAVE = range(2)

ENTER_DAILY = AlertScheduleTypeEnum.DAILY

ENTER_MONTHLY = AlertScheduleTypeEnum.MONTHLY


@inject
async def cancel(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User canceled the schedule conversation.")

    user = typing.cast(User, update.effective_user)
    text = _("User canceled the schedule conversation.")
    text = telegram_template.inline(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        text,
    )

    return ConversationHandler.END


@authorized(IS_APPROVED)
@inject
async def schedule_start(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:

    logger.info("User started schedule conversation.")

    user = typing.cast(User, update.effective_user)

    daily_btn_text = _("Daily")
    daily_btn_text = telegram_template.inline(
        daily_btn_text,
        user.language_code,
    )
    monthly_btn_text = _("Monthly")
    monthly_btn_text = telegram_template.inline(
        monthly_btn_text,
        user.language_code,
    )

    keyboard = [
        [
            InlineKeyboardButton(
                daily_btn_text,
                callback_data=str(ENTER_DAILY),
            ),
            InlineKeyboardButton(
                monthly_btn_text,
                callback_data=str(ENTER_MONTHLY),
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    response = telegram_template.render(
        "schedule/choice.html",
        user.language_code,
    )
    await send_response(
        update,
        context,
        response,
        keyboard=reply_markup,
    )

    return TIME


@authorized(IS_APPROVED)
@inject
async def schedule_inter(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:

    if update.callback_query is not None:
        query = update.callback_query.data

    if context.chat_data is not None:
        context.chat_data["choicen_type"] = query#TODO 128 str

    user = typing.cast(User, update.effective_user)
    message = telegram_template.render(
        "schedule/schedule.html",
        user.language_code,
    )
    await send_response(
        update,
        context,
        message,
    )
    return SAVE


# TODO add transactions
@inject
async def enter_time(
    update: Update,
    context: CustomContext,
    schedule_dal: dal.AlertScheduleAsyncDAL = Provide[BotContainer.schedule_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:

    logger.info("User entered schedule.")

    user_data = typing.cast(dict, context.user_data)
    chat_data = typing.cast(dict, context.chat_data)
    user_id = user_data["user"].id
    choicen_type = chat_data["choicen_type"]
    user = typing.cast(User, update.effective_user)
    schedule_type = AlertScheduleTypeEnum(int(choicen_type))
    message = typing.cast(Message, update.message)
    text = typing.cast(str, message.text)
    enter = text.strip()
    when = datetime.strptime(enter, "%H:%M").time()

    schedule = schedule_dal.filter(user_id=user_id, period=schedule_type).load_related("task_log")

    schedule_obj = await schedule.first()

    if schedule_obj.task_log is not None:

        redefine_alert_task.delay(str(schedule_obj.task_log.id), when, user.id, schedule_type)

    await schedule.update(when=when)

    text = telegram_template.render(
        "schedule/time.html",
        user.language_code,
        cancel=False,
    )
    await send_response(
        update,
        context,
        text,
    )

    return ConversationHandler.END


schedule_conv = ConversationHandler(
    persistent=True,
    name="schedule",
    entry_points=[CommandHandler("schedule", schedule_start)],
    states={
        TIME: [CallbackQueryHandler(schedule_inter)],
        SAVE: [MessageHandler(IS_VALID_TIME_FILTER, enter_time)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
