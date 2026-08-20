import base64
import logging
import traceback
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
import asyncio
from helpers import app_state
from settings import BATCH_LIMIT, BIN_CHANNEL, LOG_CHANNEL
from keyboards import ButtonStyle

def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    return base64_bytes.decode("ascii").rstrip("=")

def decode(base64_string):
    try:
        base64_string = base64_string.strip()
        padding = len(base64_string) % 4
        if padding:
            base64_string += "=" * (4 - padding)
        base64_bytes = base64.urlsafe_b64decode(base64_string)
        return base64_bytes.decode("ascii")
    except Exception:
        return None
        
def get_link_data(link):
    if "t.me/c/" in link:
        parts = [p for p in link.rstrip("/").split("/") if p]
        if len(parts) >= 2 and parts[-2].isdigit() and parts[-1].isdigit():
            chat_id = int("-100" + parts[-2])
            msg_id = int(parts[-1])
            return chat_id, msg_id
    return None, None

@Client.on_message(filters.command("batch") & filters.private)
async def batch_handler(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text(
                   "❌ USAGE: /batch <first_post_link> <last_post_link>"
               )

    status_msg = await message.reply_text("⚙️ **ᴄʜᴇᴄᴋɪɴɢ ʀᴀɴɢᴇ....**")

    link1 = message.command[1]
    link2 = message.command[2]
    user = message.from_user

    try:
        chat_id1, msg_id1 = get_link_data(link1)
        chat_id2, msg_id2 = get_link_data(link2)

        if chat_id1 != chat_id2:
             return await status_msg.edit("❌ **Eʀʀᴏʀ:** Dᴏɴᴏ ʟɪɴᴋ sᴀᴍᴇ ᴄʜᴀɴɴᴇʟ ᴋᴇ ʜᴏɴᴇ ᴄʜᴀʜɪʏᴇ.")

        start_id = min(msg_id1, msg_id2)
        end_id = max(msg_id1, msg_id2)
        total_files = end_id - start_id + 1

        if total_files > BATCH_LIMIT:
            return await status_msg.edit(
                f"❌ **Lɪᴍɪᴛ Exᴄᴇᴇᴅᴇᴅ!**\n\n"
                f"⚠️ Aᴀᴘ ᴇᴋ ʙᴀᴀʀ ᴍᴇɪɴ sɪʀғ **{BATCH_LIMIT} ғɪʟᴇs** ᴋᴀ ʙᴀᴛᴄʜ ʙᴀɴᴀ sᴀᴋᴛᴇ ʜᴀɪɴ.\n"
                f"🔢 Aᴀᴘɴᴇ **{total_files} ᴍᴇssᴀɢᴇs** sᴇʟᴇᴄᴛ ᴋɪʏᴇ ʜᴀɪɴ."
            )

        await status_msg.edit(f"🔄 **Pʀᴏᴄᴇssɪɴɢ {total_files} ғɪʟᴇs...**")

        bin_ids = []

        for i in range(start_id, end_id + 1):
            try:
                msg = await client.get_messages(chat_id1, i)
                if msg and not msg.empty:
                    if msg.document or msg.video or msg.audio:
                        fwd_msg = await msg.forward(BIN_CHANNEL)
                        bin_ids.append(fwd_msg.id)
                        await asyncio.sleep(1) 
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                continue

        if not bin_ids:
            return await status_msg.edit("❌ **Nᴏ ᴍᴇᴅɪᴀ ғᴏᴜɴᴅ ɪɴ ʀᴀɴɢᴇ.**")

        first_bin_id = bin_ids[0]
        last_bin_id = bin_ids[-1]

        raw_payload = f"batch-{first_bin_id}-{last_bin_id}"
        encoded_payload = encode(raw_payload)
        
        link = f"https://t.me/{app_state.U_NAME}?start={encoded_payload}"
        
        await status_msg.edit(
            f"🔐 **Bᴀᴛᴄʜ Lɪɴᴋ Cʀᴇᴀᴛᴇᴅ!**\n\n"
            f"📂 **Fɪʟᴇs:** {len(bin_ids)}\n"
            f"⚠️ **Lɪᴍɪᴛ:** Mᴀx {BATCH_LIMIT} ғɪʟᴇs ᴘᴇʀ ʟɪɴᴋ\n\n"
            f"🔗 **Lɪɴᴋ:** {link}"
        )
        
        try:
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=f"#BATCH_SAVE:\n\n👤 User: {user.mention} (`{user.id}`)\n🔢 Files: {len(bin_ids)}\n🔗 Generated Batch Link!",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📂 Open Link", url=link, style=ButtonStyle.SUCCESS)]])
            )
        except Exception as e:
            logging.error(f"Failed to send log: {e}")

    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")

        try:
            error_traceback = traceback.format_exc()
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=(
                    f"#BATCH_ERROR:\n\n"
                    f"👤 **User:** {user.mention} (`{user.id}`)\n"
                    f"❌ **Error:** `{e}`\n\n"
                    f"📜 **Traceback:**\n`{error_traceback[:1000]}`"
                )
            )
        except Exception as log_error:
            logging.error(f"Could not send error log: {log_error}")
            
