from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

try:
    from pyrogram.enums import ButtonStyle
except ImportError:
    class ButtonStyle:
        PRIMARY = 0
        SUCCESS = 0
        DANGER = 0

from config import CHANNEL, SUPPORT
from helpers import app_state

__all__ = ["ButtonStyle", "_start_markup"]

DEV_URL = "https://t.me/DmOwner"


def _bot_username() -> str:
    return app_state.U_NAME or "bot"


def _start_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add Me To Your Channel",
                    url=f"http://t.me/{_bot_username()}?startchannel=true",
                    style=ButtonStyle.SUCCESS,
                )
            ],
            [
                InlineKeyboardButton("📢 Updates Channel", url=CHANNEL, style=ButtonStyle.PRIMARY),
                InlineKeyboardButton("👥 Support Group",   url=SUPPORT, style=ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("❓ Help",   callback_data="help",  style=ButtonStyle.PRIMARY),
                InlineKeyboardButton("ℹ️ About", callback_data="about", style=ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("👨‍💻 DEV", url=DEV_URL, style=ButtonStyle.DANGER)
            ],
        ]
    )