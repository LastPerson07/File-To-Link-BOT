import asyncio
import html
import logging
from api.helpers.file_meta import get_hash
from pyrogram import Client, filters, enums
from settings import BIN_CHANNEL, URL
from database.store import store
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import ButtonStyle

@Client.on_message(filters.channel & (filters.document | filters.video) & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot: Client, broadcast: Message):
    for attempt in range(3):
        try:
            await _forward_channel_media(bot, broadcast)
            return
        except asyncio.exceptions.TimeoutError:
            logging.warning(f"Request Timed Out! Retry {attempt + 1}/3...")
            await asyncio.sleep(5)
        except FloodWait as w:
            logging.warning(f"Sleeping for {w.value}s due to FloodWait")
            await asyncio.sleep(w.value)
            return
        except Exception as e:
            await bot.send_message(chat_id=BIN_CHANNEL, text=f"❌ **Error:** `{e}`", disable_web_page_preview=True)
            logging.error(f"Can't edit channel message! Error: {e}")
            return
    logging.error(f"Gave up forwarding channel media {broadcast.id} after 3 timeouts")


async def _forward_channel_media(bot: Client, broadcast: Message):
    chat_id = broadcast.chat.id
    if str(chat_id).startswith("-100"):
        is_banned = await store.is_channel_blocked(chat_id)
        if is_banned:
            try:
                await bot.send_message(
                    chat_id,
                    "🚫 **Tʜɪꜱ ᴄʜᴀɴɴᴇʟ ɪꜱ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜꜱɪɴɢ ᴛʜᴇ ʙᴏᴛ.**\n\n"
                    "🔄 **Cᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪғ ʏᴏᴜ ᴛʜɪɴᴋ ᴛʜɪꜱ ɪꜱ ᴀ ᴍɪꜱᴛᴀᴋᴇ.**\n\n@LastPerson07"
                )
            except Exception:
                pass
            await bot.leave_chat(chat_id)
            return
    msg = await broadcast.forward(chat_id=BIN_CHANNEL)
    stream = f"{URL}watch/{msg.id}/lastperson07.mkv?hash={get_hash(msg)}"
    download = f"{URL}{msg.id}?hash={get_hash(msg)}"
    await msg.reply_text(
        text=f"**Channel Name:** `{broadcast.chat.title}`\n**CHANNEL ID:** `{broadcast.chat.id}`\n**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {stream}",
        quote=True
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ ꜱᴛʀᴇᴀᴍ", url=stream, style=ButtonStyle.SUCCESS),
         InlineKeyboardButton("⬇️ ᴅᴏᴡɴʟᴏᴀᴅ", url=download, style=ButtonStyle.SUCCESS)]
    ])
    await bot.edit_message_reply_markup(
        chat_id=broadcast.chat.id,
        message_id=broadcast.id,
        reply_markup=buttons
    )

@Client.on_message(filters.command("link") & filters.group & filters.reply)
async def group_link_handler(bot: Client, message: Message):
    try:
        reply = message.reply_to_message
        if not reply or not (reply.document or reply.video):
            return await message.reply_text("❌ **Is ᴄᴏᴍᴍᴀɴᴅ ᴋᴀ ᴜsᴇ ᴋɪsɪ Vɪᴅᴇᴏ ʏᴀ Fɪʟᴇ ᴘᴀʀ Rᴇᴘʟʏ ᴋᴀʀᴋᴇ ᴋᴀʀᴇɪɴ.**")
        status_msg = await message.reply_text("🔄 **Gᴇɴᴇʀᴀᴛɪɴɢ Lɪɴᴋ... Pʟᴇᴀsᴇ ᴡᴀɪᴛ.**")
        try:
            log_msg = await reply.forward(chat_id=BIN_CHANNEL)
        except Exception as e:
            return await status_msg.edit(f"❌ Error forwarding to Bin Channel: {e}")
        file = reply.document or reply.video
        file_name = file.file_name if hasattr(file, 'file_name') and file.file_name else "Unknown File"
        stream = f"{URL}watch/{log_msg.id}/lastperson07.mkv?hash={get_hash(log_msg)}"
        download = f"{URL}{log_msg.id}?hash={get_hash(log_msg)}"
        await log_msg.reply_text(
            text=(
                f"👤 **Requested By:** {message.from_user.mention} (`{message.from_user.id}`)\n"
                f"👥 **Group Name:** {message.chat.title}\n"
                f"🆔 **Group ID:** `{message.chat.id}`\n"
                f"🔗 **Stream URL:** {stream}"
            ),
            quote=True,
            disable_web_page_preview=True
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ ꜱᴛʀᴇᴀᴍ", url=stream, style=ButtonStyle.SUCCESS),
             InlineKeyboardButton("⬇️ ᴅᴏᴡɴʟᴏᴀᴅ", url=download, style=ButtonStyle.SUCCESS)]
        ])
        await status_msg.edit_text(
            text=f"📂 <b>𝘍𝘪𝘭𝘦 𝘕𝘢𝘮𝘦:</b> {html.escape(file_name)}\n\n🔗 <b>𝘓𝘪𝘯𝘬𝘴 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺!</b>",
            reply_markup=buttons,
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        logging.error(f"Group Link Error: {e}")
        await message.reply_text(f"❌ Error: `{e}`")
        
