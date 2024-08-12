import math
import typing

import structlog
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from telegram import CallbackQuery
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram import User
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler

from core import dal
from infrastructure.bot.container import BotContainer
from infrastructure.bot.decorators import authorized
from infrastructure.bot.keyboards import get_paginated_list_keyboard
from infrastructure.bot.permissions import IS_ADMIN
from infrastructure.bot.permissions import IS_APPROVED
from infrastructure.bot.templates import TelegramTemplate
from utils.lang import _
from utils.pagination import PageSizePagination
from utils.telegram.callback import get_postfix
from utils.telegram.context import CustomContext
from utils.telegram.response import send_response

logger = structlog.get_logger()

PAGE_SIZE = 5

(
    SELECT_ADMIN_OPTIONS,
    SELECT_USER_OPTIONS,
    SELECT_REQUEST_OPTIONS,
    ADMIN_USERS,
    ADMIN_REQUESTS,
) = range(5)

ADMIN_USERS_DETAIL = "admin_users_detail_"
ADMIN_USERS_BAN = "admin_users_ban_"
ADMIN_USERS_MAKE_ADMIN = "admin_users_make_admin_"
ADMIN_USERS_REMOVE_ADMIN = "admin_users_remove_admin_"
ADMIN_USERS_LIST = "admin_users_list_"
ADMIN_REQUESTS_DETAIL = "admin_requests_detail_"
ADMIN_REQUESTS_APPROVED = "admin_requests_approved_"
ADMIN_REQUESTS_LIST = "admin_requests_list_"
END = ConversationHandler.END


def _get_options_keyboard(telegram_template: TelegramTemplate, locale: str | None = None) -> InlineKeyboardMarkup:
    users_btn_text = _("Users")
    users_btn_text = telegram_template.inline(
        users_btn_text,
        locale,
    )
    requests_btn_text = _("Requests")
    requests_btn_text = telegram_template.inline(
        requests_btn_text,
        locale,
    )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    users_btn_text,
                    callback_data=ADMIN_USERS_LIST,
                )
            ],
            [
                InlineKeyboardButton(
                    requests_btn_text,
                    callback_data=ADMIN_REQUESTS_LIST,
                )
            ],
        ]
    )


async def admin_start_unapproved_fallback(
    _: Update,
    __: CustomContext,
) -> int:
    logger.info("Unapproved user tried to start admin command.")

    return END


@inject
async def admin_start_not_admin_fallback(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User tried to start admin command without permissions.")

    user = typing.cast(User, update.effective_user)
    text = _("You have no permission to do that.")
    message = telegram_template.render_error(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        message,
    )

    return END


@authorized(IS_APPROVED, admin_start_unapproved_fallback)
@authorized(IS_ADMIN, admin_start_not_admin_fallback)
@inject
async def admin_start(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User started admin conversation.")

    user = typing.cast(User, update.effective_user)
    message = telegram_template.render(
        "admin/greet.html",
        user.language_code,
    )
    await send_response(
        update,
        context,
        message,
        keyboard=_get_options_keyboard(
            telegram_template,
            user.language_code,
        ),
    )

    return SELECT_ADMIN_OPTIONS


@inject
async def admin_users_list(
    update: Update,
    __: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User started admin / users conversation.")

    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    current_page_num = get_postfix(query_data, ADMIN_USERS_LIST, 1, int)
    pagination = PageSizePagination(page_size=PAGE_SIZE, page=current_page_num)
    cursor = user_dal.exclude(tg_id__exact=user.id).order_by(created_at=True).paginate(pagination)
    point, items = await cursor.next()
    total_pages = math.ceil(point.count / PAGE_SIZE)

    paginated_list_keyboard = get_paginated_list_keyboard(
        current_page=current_page_num,
        total_pages=total_pages,
        items=items,
        item_title_getter=lambda item: item.full_name,
        item_id_getter=lambda item: item.id,
        item_prefix_callback=ADMIN_USERS_DETAIL,
        base_prefix=ADMIN_USERS_LIST,
    )

    keyboard.extend(paginated_list_keyboard)

    keyboard.append(
        [
            InlineKeyboardButton(
                telegram_template.inline(_("Back"), user.language_code),
                callback_data=END,
            )
        ]
    )

    message = telegram_template.render(
        "admin/users.html",
        user.language_code,
        count=point.count,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADMIN_USERS


@inject
async def admin_users_detail(
    update: Update,
    __: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    user_id: str = get_postfix(
        query_data,
        ADMIN_USERS_DETAIL,
    )
    selected_user = await user_dal.filter(id=user_id).first()

    # TODO: handle case
    if not selected_user:
        return ADMIN_USERS

    logger.info(f"Selected user {user_id=!s} in admin / users conversation.")

    back_btn_text = _("Back")
    back_btn_text = telegram_template.inline(
        back_btn_text,
        user.language_code,
    )
    ban_btn_text = _("Ban")
    ban_btn_text = telegram_template.inline(
        ban_btn_text,
        user.language_code,
    )
    make_admin_btn_text = _("Make admin")
    make_admin_btn_text = telegram_template.inline(
        make_admin_btn_text,
        user.language_code,
    )
    remove_admin_btn_text = _("Remove admin")
    remove_admin_btn_text = telegram_template.inline(
        remove_admin_btn_text,
        user.language_code,
    )
    keyboard.extend(
        [
            (
                [
                    InlineKeyboardButton(
                        ban_btn_text,
                        callback_data=f"{ADMIN_USERS_BAN}{user_id}",
                    )
                ]
                if selected_user.approved
                else []
            ),
            (
                (
                    [
                        InlineKeyboardButton(
                            remove_admin_btn_text,
                            callback_data=f"{ADMIN_USERS_REMOVE_ADMIN}{user_id}",
                        )
                    ]
                    if selected_user.admin
                    else [
                        InlineKeyboardButton(
                            make_admin_btn_text,
                            callback_data=f"{ADMIN_USERS_MAKE_ADMIN}{user_id}",
                        )
                    ]
                )
                if selected_user.approved
                else []
            ),
            [
                InlineKeyboardButton(
                    back_btn_text,
                    callback_data=END,
                )
            ],
        ]
    )

    message = telegram_template.render(
        "admin/user.html",
        user.language_code,
        user=selected_user,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADMIN_USERS


@inject
async def admin_users_ban(
    update: Update,
    __: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    user_id: str = get_postfix(
        query_data,
        ADMIN_USERS_BAN,
    )

    selected_user = await user_dal.filter(id=user_id).update(approved=False, admin=False)

    # TODO: handle case
    if not selected_user:
        return ADMIN_USERS

    logger.info(f"User {user_id=!s} was approved.")

    back_btn_text = _("Back")
    back_btn_text = telegram_template.inline(
        back_btn_text,
        user.language_code,
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                back_btn_text,
                callback_data=END,
            )
        ]
    )

    message = telegram_template.render(
        "admin/ban.html",
        user.language_code,
        user=selected_user,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADMIN_USERS


@inject
async def admin_users_make_admin(
    update: Update,
    context: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    user_id: str = get_postfix(
        query_data,
        ADMIN_USERS_MAKE_ADMIN,
    )
    selected_user = await user_dal.filter(id=user_id).update(admin=True)

    # TODO: handle case
    if not selected_user:
        return ADMIN_USERS

    logger.info(f"User {user_id=!s} was upgraded to admin.")

    back_btn_text = _("Back")
    back_btn_text = telegram_template.inline(
        back_btn_text,
        user.language_code,
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                back_btn_text,
                callback_data=END,
            )
        ]
    )

    message = telegram_template.render(
        "admin/make_admin.html",
        user.language_code,
        user=selected_user,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    make_admin_text = _("Congratulation! You are now admin.")
    make_admin_text = telegram_template.inline(make_admin_text, selected_user.language_code)

    try:
        await context.bot.send_message(selected_user.tg_id, make_admin_text)
    except Forbidden:
        pass

    return ADMIN_USERS


@inject
async def admin_users_remove_admin(
    update: Update,
    __: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    user_id: str = get_postfix(
        query_data,
        ADMIN_USERS_REMOVE_ADMIN,
    )
    selected_user = await user_dal.filter(id=user_id).update(admin=False)

    # TODO: handle case
    if not selected_user:
        return ADMIN_USERS

    logger.info(f"User {user_id=!s} was removed admin permissions.")

    back_btn_text = _("Back")
    back_btn_text = telegram_template.inline(
        back_btn_text,
        user.language_code,
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                back_btn_text,
                callback_data=END,
            )
        ]
    )

    message = telegram_template.render(
        "admin/remove_admin.html",
        user.language_code,
        user=selected_user,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADMIN_USERS


@inject
async def admin_requests_list(
    update: Update,
    __: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User started admin / requests conversation.")

    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    current_page_num = get_postfix(query_data, ADMIN_REQUESTS_LIST, 1, int)
    pagination = PageSizePagination(page_size=PAGE_SIZE, page=current_page_num)
    cursor = user_dal.filter(approved__exact=False).order_by(created_at=True).paginate(pagination)
    point, items = await cursor.next()
    total_pages = math.ceil(point.count / PAGE_SIZE)

    paginated_list_keyboard = get_paginated_list_keyboard(
        current_page=current_page_num,
        total_pages=total_pages,
        items=items,
        item_title_getter=lambda item: item.full_name,
        item_id_getter=lambda item: item.id,
        item_prefix_callback=ADMIN_REQUESTS_DETAIL,
        base_prefix=ADMIN_REQUESTS_LIST,
    )

    keyboard.extend(paginated_list_keyboard)

    back_btn_text = _("Back")
    back_btn_text = telegram_template.inline(back_btn_text, user.language_code)
    keyboard.append(
        [
            InlineKeyboardButton(
                back_btn_text,
                callback_data=END,
            )
        ]
    )

    message = telegram_template.render(
        "admin/requests.html",
        user.language_code,
        count=point.count,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADMIN_REQUESTS


@inject
async def admin_requests_detail(
    update: Update,
    __: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    user_id: str = get_postfix(
        query_data,
        ADMIN_REQUESTS_DETAIL,
    )
    selected_user = await user_dal.filter(id=user_id).first()

    # TODO: handle case
    if not selected_user:
        return ADMIN_REQUESTS

    logger.info(f"Selected user {user_id} in admin / requests conversation.")

    yes_btn_text = _("Yes")
    yes_btn_text = telegram_template.inline(
        yes_btn_text,
        user.language_code,
    )
    back_btn_text = _("Back")
    back_btn_text = telegram_template.inline(
        back_btn_text,
        user.language_code,
    )
    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    yes_btn_text,
                    callback_data=f"{ADMIN_REQUESTS_APPROVED}{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    back_btn_text,
                    callback_data=END,
                )
            ],
        ]
    )

    message = telegram_template.render(
        "admin/request.html",
        user.language_code,
        user=selected_user,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADMIN_REQUESTS


@inject
async def admin_requests_approved(
    update: Update,
    context: CustomContext,
    user_dal: dal.UserAsyncDAL = Provide[BotContainer.user_async_dal],
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    keyboard = []

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)
    query_data = typing.cast(str, query.data)

    await query.answer()

    user_id: str = get_postfix(
        query_data,
        ADMIN_REQUESTS_APPROVED,
    )
    selected_user = await user_dal.filter(id=user_id).update(approved=True)

    # TODO: handle case
    if not selected_user:
        return ADMIN_REQUESTS

    logger.info(f"User {user_id=!s} was approved.")

    back_btn_text = _("Back")
    back_btn_text = telegram_template.inline(
        back_btn_text,
        user.language_code,
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                back_btn_text,
                callback_data=END,
            )
        ]
    )

    message = telegram_template.render(
        "admin/approved.html",
        user.language_code,
        user=selected_user,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    approved_text = _("Congratulation! You are now approved.")
    approved_text = telegram_template.inline(approved_text, selected_user.language_code)

    try:
        await context.bot.send_message(selected_user.tg_id, approved_text)
    except Forbidden:
        pass

    return ADMIN_REQUESTS


@inject
async def cancel(
    update: Update,
    context: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User canceled the admin conversation.")

    user = typing.cast(User, update.effective_user)
    text = _("Bye! I hope we can talk again some day.")
    response = telegram_template.inline(
        text,
        user.language_code,
    )

    await send_response(
        update,
        context,
        response,
    )

    return END


@inject
async def end_users_conv(
    update: Update,
    __: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info('User canceled the "users" conversation.')

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)

    await query.answer()

    message = telegram_template.render(
        "admin/greet.html",
        user.language_code,
    )
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=_get_options_keyboard(
            telegram_template,
            user.language_code,
        ),
    )

    return END


@inject
async def end_requests_conv(
    update: Update,
    __: CustomContext,
    telegram_template: TelegramTemplate = Provide[BotContainer.telegram_template],
) -> int:
    logger.info("User canceled the admin / requests conversation.")

    user = typing.cast(User, update.effective_user)
    query = typing.cast(CallbackQuery, update.callback_query)

    await query.answer()

    message = telegram_template.render(
        "admin/greet.html",
        user.language_code,
    )

    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=_get_options_keyboard(
            telegram_template,
            user.language_code,
        ),
    )

    return END


users_conv = ConversationHandler(
    persistent=True,
    name="admin_users",
    entry_points=[CallbackQueryHandler(admin_users_list, rf"^{ADMIN_USERS_LIST}(\d+)?$")],
    states={
        ADMIN_USERS: [
            CallbackQueryHandler(admin_users_detail, rf"^{ADMIN_USERS_DETAIL}(.+)?$"),
            CallbackQueryHandler(admin_users_ban, rf"^{ADMIN_USERS_BAN}(.+)?$"),
            CallbackQueryHandler(admin_users_make_admin, rf"^{ADMIN_USERS_MAKE_ADMIN}(.+)?$"),
            CallbackQueryHandler(admin_users_remove_admin, rf"^{ADMIN_USERS_REMOVE_ADMIN}(.+)?$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(end_users_conv, pattern="^" + str(END) + "$")],
    map_to_parent={
        END: SELECT_ADMIN_OPTIONS,
    },
)
requests_conv = ConversationHandler(
    persistent=True,
    name="admin_requests",
    entry_points=[CallbackQueryHandler(admin_requests_list, rf"^{ADMIN_REQUESTS_LIST}(\d+)?$")],
    states={
        ADMIN_REQUESTS: [
            CallbackQueryHandler(admin_requests_detail, rf"^{ADMIN_REQUESTS_DETAIL}(.+)?$"),
            CallbackQueryHandler(admin_requests_approved, rf"^{ADMIN_REQUESTS_APPROVED}(.+)?$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(end_requests_conv, pattern="^" + str(END) + "$")],
    map_to_parent={
        END: SELECT_ADMIN_OPTIONS,
    },
)
admin_conv = ConversationHandler(
    persistent=True,
    name="admin",
    entry_points=[CommandHandler("admin", admin_start)],
    states={
        SELECT_ADMIN_OPTIONS: [
            users_conv,
            requests_conv,
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
