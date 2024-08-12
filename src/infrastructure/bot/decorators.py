import functools
import typing

from telegram import Update
from telegram._utils.types import RT
from telegram.ext._utils.types import CCT
from telegram.ext._utils.types import HandlerCallback

from utils.permissions import BasePermission


def authorized(
    permission: BasePermission,
    fallback: HandlerCallback[Update, CCT, RT] | None = None,
):
    def decorator(func: HandlerCallback[Update, CCT, RT]) -> HandlerCallback[Update, CCT, RT]:
        @functools.wraps(func)
        async def wrapper(update: Update, context: CCT, *args, **kwargs):
            user_data = typing.cast(dict, context.user_data)
            user = user_data.get("user")
            if not user:
                return

            # TODO: pass DTO
            allowed = await permission(user=user)
            if allowed:
                return await func(update, context, *args, **kwargs)

            if fallback is not None:
                return await fallback(update, context, *args, **kwargs)

        return wrapper

    return decorator
