import logging

from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ParseMode
from texts import Texts
from config import AUTH_PICS, AUTH_CHANNEL, ENABLE_LIMIT
from database.store import store
from keyboards import ButtonStyle

async def membership_check(bot, message: Message) -> bool:
    user_id = message.from_user.id
    bot_user = await bot.get_me()    
    not_joined_channels = []
    for channel_id in AUTH_CHANNEL:
        try:
            await bot.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            try:
                chat = await bot.get_chat(channel_id)
                try:
                    invite_link = await bot.export_chat_invite_link(channel_id)
                except ChatAdminRequired:
                    await message.reply_text(
                        text = (
                            "<i>🔒 Bᴏᴛ ɪs ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪs ᴄʜᴀɴɴᴇʟ.\n"
                            "Pʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ᴅᴇᴠᴇʟᴏᴘᴇʀ:</i> "
                            "<b><a href='https://t.me/LastPerson07'>[ ᴄʟɪᴄᴋ ʜᴇʀᴇ ]</a></b>"
                        ),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    return False
                not_joined_channels.append((chat.title, invite_link))
            except Exception as e:
                logging.error(f"Chat fetch failed: {e}")
                continue
        except Exception as e:
            logging.error(f"get_chat_member failed: {e}")
            continue

    if not_joined_channels:
        buttons = [
            [InlineKeyboardButton(f"[{i+1}] {title}", url=link, style=ButtonStyle.SUCCESS)]
            for i, (title, link) in enumerate(not_joined_channels)
        ]
        buttons.append([
            InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{bot_user.username}?start=start", style=ButtonStyle.PRIMARY)
        ])
        await message.reply_photo(
            photo=AUTH_PICS,
            caption=Texts.AUTH_TXT.format(message.from_user.mention),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
        return False

    return True
    
async def rate_limit_ok(user_id):
    if not ENABLE_LIMIT:
        return True, 0
    return await store.rate_limit_ok(int(user_id))
