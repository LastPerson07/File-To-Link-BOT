from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS, AUTH_CHANNEL, BIN_CHANNEL, LOG_CHANNEL, MAINTENANCE_MODE

BYPASS_IDS = ADMINS + AUTH_CHANNEL + [BIN_CHANNEL, LOG_CHANNEL]

@Client.on_message(~filters.service, group=0)
async def status_guard(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id
    if MAINTENANCE_MODE and user_id not in BYPASS_IDS and chat_id not in BYPASS_IDS:
        await message.reply(
            "🚧 **Bot is under Maintenance!**\n\nPlease try again later.\n\nSupport Group: @LastPerson07",
            quote=True
        )
        return

    await message.continue_propagation()
