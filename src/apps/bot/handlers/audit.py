import typing

import structlog
from telegram import Update
from telegram import User

from utils.telegram.context import CustomContext

logger = structlog.get_logger()


async def audit_log(update: Update, _: CustomContext) -> None:
    """
    Audit logger.
    """
    user = typing.cast(User, update.effective_user)
    sender_id = user.id

    structlog.contextvars.bind_contextvars(tg_id=sender_id)

    if update.message:
        text = update.message.text
    else:
        text = None

    logger.info("Output access log.", message=text)
