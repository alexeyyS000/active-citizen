"""
Sync Telegram Bot client.
"""

import telegram
from telebot import TeleBot

from utils.telegram.response import KeyboardType


class TelegramBotClient:
    def __init__(self, bot: TeleBot) -> None:
        self._bot = bot

    def send_response(
        self,
        chat_id: int,
        response: str,
        keyboard: KeyboardType | None = None,
        parse_mode: telegram.constants.ParseMode = telegram.constants.ParseMode.HTML,
    ) -> None:
        self._bot.send_message(
            chat_id=chat_id,
            disable_web_page_preview=True,
            text=response,
            parse_mode=parse_mode,
            reply_markup=keyboard,
        )
