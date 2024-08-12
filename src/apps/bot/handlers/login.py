import typing

import structlog
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from telegram import CallbackQuery
from telegram import Chat
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Message
from telegram import Update
from telegram import User
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import filters

from core import dal
from infrastructure.bot.container import BotContainer
from infrastructure.bot.decorators import authorized
from infrastructure.bot.permissions import IS_APPROVED
from infrastructure.bot.templates import TelegramTemplate
from utils.lang import _
from utils.telegram.context import CustomContext
from utils.telegram.response import send_response

logger = structlog.get_logger()

SAVE_CONFIRM, SAVE_REPEAT = range(2)
LOGIN, PASSWORD, SAVE = range(3)


@authorized(IS_APPROVED)
@inject
async def login_start(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User started login conversation.")

    user = typing.cast(User, update.effective_user)
    message = telegram_template.render(
        "login/greet.html",
        user.language_code,
    )

    await send_response(
        update,
        context,
        message,
    )

    return LOGIN


@inject
async def enter_login(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User entered login.")

    user = typing.cast(User, update.effective_user)
    user_data = typing.cast(dict, context.user_data)
    message = typing.cast(Message, update.message)
    text = typing.cast(str, message.text)

    enter = text.strip()
    user_data["login"] = enter
    user_data["login_msg_id"] = message.id

    text = telegram_template.render(
        "login/password.html",
        user.language_code,
    )
    await send_response(
        update,
        context,
        text,
    )

    return PASSWORD


@inject
async def enter_password(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User entered password.")

    user = typing.cast(User, update.effective_user)
    user_data = typing.cast(dict, context.user_data)
    message = typing.cast(Message, update.message)
    text = typing.cast(str, message.text)

    enter = text.strip()
    user_data["password"] = enter
    user_data["password_msg_id"] = message.id

    yes_btn_text = _("Yes")
    yes_btn_text = telegram_template.inline(
        yes_btn_text,
        user.language_code,
    )
    no_btn_text = _("No")
    no_btn_text = telegram_template.inline(
        no_btn_text,
        user.language_code,
    )
    keyboard = [
        [
            InlineKeyboardButton(
                yes_btn_text,
                callback_data=str(SAVE_CONFIRM),
            ),
            InlineKeyboardButton(
                no_btn_text,
                callback_data=str(SAVE_REPEAT),
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    response = telegram_template.render(
        "login/confirm.html",
        user.language_code,
    )
    await send_response(
        update,
        context,
        response,
        keyboard=reply_markup,
    )

    return SAVE


@inject
async def save_credential(
    update: Update,
    context: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    mos_ru_user_dal: dal.MosRuUserAsyncDAL = Provide[BotContainer.mos_ru_user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    chat = typing.cast(Chat, update.effective_chat)
    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    user_data = typing.cast(dict, context.user_data)

    login = user_data["login"]
    password = user_data["password"]
    login_msg_id = user_data["login_msg_id"]
    password_msg_id = user_data["password_msg_id"]

    mos_ru_user = await mos_ru_user_dal.create_one(login=login, password=password)
    await user_dal.filter(tg_id=user.id).update(mos_ru_user_id=mos_ru_user.id)

    logger.info("Saved entered credentials.")

    # Delete messages with credentials
    await context.bot.delete_message(
        chat.id,
        login_msg_id,
    )
    await context.bot.delete_message(
        chat.id,
        password_msg_id,
    )

    logger.info("Messages with credentials were deleted.")

    response = telegram_template.render(
        "login/save.html",
        user.language_code,
        cancel=False,
    )
    await send_response(
        update,
        context,
        response,
    )

    await query.answer()

    return ConversationHandler.END


@inject
async def repeat(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("Repeat login conversation.")

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)

    text = telegram_template.render(
        "login/greet.html",
        user.language_code,
    )
    await send_response(
        update,
        context,
        text,
    )

    await query.answer()

    return LOGIN


@inject
async def cancel(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User canceled the login conversation.")

    user = typing.cast(User, update.effective_user)
    text = _("Bye! I hope we can talk again some day.")
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


login_conv = ConversationHandler(
    persistent=True,
    name="login",
    entry_points=[CommandHandler("login", login_start)],
    states={
        LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_login)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)],
        SAVE: [
            CallbackQueryHandler(repeat, pattern="^" + str(SAVE_REPEAT) + "$"),
            CallbackQueryHandler(save_credential, pattern="^" + str(SAVE_CONFIRM) + "$"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
