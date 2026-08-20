import time
import asyncio
import html
import logging
import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from settings import URL, BIN_CHANNEL, FSUB, MAX_FILES
from database.store import store
from api.helpers.file_meta import get_hash
from helpers import humanbytes
from plugins.checks import rate_limit_ok, membership_check
from texts import Texts
from keyboards import ButtonStyle

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio), group=4)
async def private_receive_handler(c: Client, m: Message):
    user_id = m.from_user.id
    if FSUB and not await membership_check(c, m):
        return

    is_banned = await store.is_user_blocked(user_id)
    if is_banned:
        await m.reply(
            "🚫 **Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ.**\n\n"
            "🔄 **Cᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪғ ʏᴏᴜ ᴛʜɪɴᴋ ᴛʜɪꜱ ɪꜱ ᴀ ᴍɪsᴛᴀᴋᴇ.**\n\n@LastPerson07"
        )
        return

    is_allowed, remaining_time = await rate_limit_ok(user_id)
    if not is_allowed:
        await m.reply_text(
            f"🚫 **Yᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ꜱᴇɴᴛ {MAX_FILES} ғɪʟᴇꜱ!**\n"
            f"Pʟᴇᴀꜱᴇ **{remaining_time} Sᴇᴄᴏɴᴅꜱ** ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ।",
            quote=True
        )
        return

    file_id = m.document or m.video or m.audio
    file_name = file_id.file_name if file_id.file_name else f"File_{int(time.time())}.mkv"
    file_size = humanbytes(file_id.file_size)

    try:
        forwarded = await m.forward(chat_id=BIN_CHANNEL)
        hash_str = get_hash(forwarded)
        stream = f"{URL}watch/{forwarded.id}/{urllib.parse.quote(file_name, safe='')}?hash={hash_str}"
        download = f"{URL}{forwarded.id}?hash={hash_str}"

        await store.files.insert_one({
            "user_id": user_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_id": forwarded.id,
            "hash": hash_str,
            "timestamp": time.time()
        })

        await forwarded.reply_text(
            f"Requested By: [{m.from_user.first_name}](tg://user?id={user_id})\n"
            f"User ID: {user_id}\nStream Link: {stream}",
            disable_web_page_preview=True,
            quote=True
        )

        await m.reply_text(
            Texts.CAPTION_TXT.format(html.escape(file_name), file_size, stream, download),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ ꜱᴛʀᴇᴀᴍ", url=stream, style=ButtonStyle.SUCCESS),
                 InlineKeyboardButton("⬇️ ᴅᴏᴡɴʟᴏᴀᴅ", url=download, style=ButtonStyle.SUCCESS)]
            ])
        )

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await c.send_message(BIN_CHANNEL, f"⚠️ FloodWait: {e.value}s from {m.from_user.first_name}")
    except Exception as e:
        logging.error(f"File link generation failed for user {user_id}: {e}", exc_info=True)
        await m.reply_text(f"❌ **Could not generate link.** Please try again.\n`{e}`", quote=True)