import asyncio
import logging
import html
from texts import Texts
from database.store import store
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from settings import (
    LOG_CHANNEL, FSUB, BIN_CHANNEL,
    CHANNEL, PICS, FILE_PIC, FILE_CAPTION
)
from plugins.checks import membership_check
from plugins.bulk_mode import decode
from api.helpers import about_text
from helpers import app_state, cleanup_after_delay
from keyboards import ButtonStyle, _start_markup

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    await message.react(emoji="😎", big=True)

    user_id = message.from_user.id
    mention = message.from_user.mention
    if len(message.command) > 1:
        argument = message.command[1]
    else:
        argument = None

    if FSUB:
        try:
            if not await membership_check(client, message):
                return
        except FloodWait as e:
            await asyncio.sleep(e.value)
            if not await membership_check(client, message):
                return

    user_existed = await store.is_user_exist(user_id)
    if not user_existed:
        await store.add_user(user_id, message.from_user.first_name)
        try:
            await client.send_message(
                LOG_CHANNEL,
                Texts.LOG_TEXT.format(user_id, mention),
            )
        except Exception:
            logger.error("LOG_CHANNEL send failed", exc_info=True)

    if argument == "help":
        buttons = [[InlineKeyboardButton("❓ Help", callback_data="help", style=ButtonStyle.PRIMARY),
                    InlineKeyboardButton("❌ Close", callback_data="close_data", style=ButtonStyle.DANGER)]]
        await message.reply_text(
            text=Texts.HELP2_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
        return

    if not argument or argument == "start":
        await message.reply_photo(
            photo=PICS,
            caption=Texts.START_TXT.format(mention),
            reply_markup=_start_markup(),
        )
        return

    if argument and argument != "start":
        try:
            decoded_data = decode(argument)
        except Exception:
            return # Ignore invalid arguments

        if decoded_data and decoded_data.startswith("batch-"):
            if FSUB:
                 if not await membership_check(client, message):
                     return

            try:
                _, start_id, end_id = decoded_data.split("-")
                start_id = int(start_id)
                end_id = int(end_id)
                status_msg = await message.reply_text(
                    "🔄 **𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨 𝘉𝘢𝘵𝘤𝘩 𝘙𝘦𝘲𝘶𝘦𝘴𝘵...**\n"
                    "<i>𝘚𝘦𝘯𝘥𝘪𝘯𝘨 𝘺𝘰𝘶𝘳 𝘧𝘪𝘭𝘦𝘴 </i>"
                )
                for i in range(start_id, end_id + 1):
                    try:
                        msg_obj = await client.get_messages(int(BIN_CHANNEL), i)
                        if not msg_obj or msg_obj.empty: continue
                        
                        file_name = "File"
                        if msg_obj.video: file_name = msg_obj.video.file_name
                        elif msg_obj.document: file_name = msg_obj.document.file_name
                        elif msg_obj.audio: file_name = msg_obj.audio.file_name
                        if not file_name: file_name = "File"
                        caption = FILE_CAPTION.format(CHANNEL, html.escape(file_name))
                        file_btn = InlineKeyboardMarkup(
                            [[InlineKeyboardButton("🔴 ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ & ғᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ 🔴",
                                                    callback_data=f"stream#{i}",
                                                    style=ButtonStyle.SUCCESS)]]
                        )
                        sent_msg = await client.copy_message(
                            chat_id=user_id,
                            from_chat_id=int(BIN_CHANNEL),
                            message_id=i,
                            caption=caption,
                            reply_markup=file_btn
                        )
                        asyncio.create_task(cleanup_after_delay(sent_msg, 600)) 
                        await asyncio.sleep(1.5)

                    except FloodWait as e:
                        await status_msg.edit(f"⏳ **High Traffic:** Waiting {e.value}s...")
                        await asyncio.sleep(e.value + 2)
                    except Exception:
                        pass
                await status_msg.delete()
                warn_msg = await message.reply_text(
                    "✅ 𝖠𝗅𝗅 𝖥𝗂𝗅𝖾𝗌 𝖢𝗈𝗆𝗉𝗅𝖾𝗍𝖾 😁!\n\n"
                    "⚠️ 𝖨𝖬𝖯𝖮𝖱𝖳𝖠𝖭𝖳: 𝖥𝗂𝗅𝖾𝗌 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖣𝖤𝖫𝖤𝖳𝖤𝖣 𝗂𝗇 10 𝖬𝗂𝗇𝗎𝗍𝖾𝗌.\n"
                    "📥 𝖥𝗈𝗋𝗐𝖺𝗋𝖽 𝗍𝗈 𝖲𝖺𝗏𝖾𝖽 𝖬𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝖭𝖮𝖶!"
                )
                asyncio.create_task(cleanup_after_delay(warn_msg, 600))
                return
            except Exception as e:
                await message.reply_text(f"❌ Error: {e}")
                return

        if argument.startswith("file_"):
            if FSUB:
                 if not await membership_check(client, message):
                     return

            try:
                _, file_id = argument.split("_", 1)
                file_id = int(file_id)
            except ValueError:
                return await message.reply("<b>⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘍𝘪𝘭𝘦 𝘓𝘪𝘯𝘬!</b>")

            try:
                original_message = await client.get_messages(int(BIN_CHANNEL), file_id)
                if not original_message or original_message.empty:
                    return await message.reply("<b>⚠️ 𝘍𝘪𝘭𝘦 𝘯𝘰𝘵 𝘧𝘰𝘶𝘯𝘥!</b>")
                media = original_message.document or original_message.video or original_message.audio
                caption = None
                if media:
                    file_name = getattr(media, "file_name", "Unnamed File") or "Unnamed File"
                    caption = FILE_CAPTION.format(CHANNEL, html.escape(file_name))
                btn_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔴 ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ & ғᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ 🔴",
                                            callback_data=f"stream#{file_id}",
                                            style=ButtonStyle.SUCCESS)]]
                )
                sent_msg = await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=int(BIN_CHANNEL),
                    message_id=file_id,
                    caption=caption,
                    reply_markup=btn_markup
                )
            except Exception:
                return await message.reply("<b>⚠️ 𝘍𝘪𝘭𝘦 𝘯𝘰𝘵 𝘧𝘰𝘶𝘯𝘥!</b>")
            warn_msg = await message.reply_text(
            "⚠️ 𝖨𝖬𝖯𝖮𝖱𝖳𝖠𝖭𝖳: 𝖥𝗂𝗅𝖾 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖣𝖤𝖫𝖤𝖳𝖤𝖣 𝗂𝗇 10 𝖬𝗂𝗇𝗎𝗍𝖾𝗌.\n"
            "📥 𝖥𝗈𝗋𝖺𝗋𝖽 𝗍𝗈 𝖲𝖺𝗏𝖾𝖽 𝖬𝖾𝗌𝗌𝖺𝗀𝖾𝗌!",
            quote=True
            )
            asyncio.create_task(cleanup_after_delay(sent_msg, 600)) 
            asyncio.create_task(cleanup_after_delay(warn_msg, 600))
            return

@Client.on_message(filters.command("about"))
async def about(client, message):
    buttons = [[
       InlineKeyboardButton('💻 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ', url='https://github.com/LastPerson07/File-To-Link-BOT', style=ButtonStyle.PRIMARY)
    ],[
       InlineKeyboardButton('❌ ᴄʟᴏsᴇ', callback_data='close_data', style=ButtonStyle.DANGER)
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(
        text=about_text(app_state.B_NAME),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )


@Client.on_message(filters.command("help"))
async def help(client, message):
    btn = [[
       InlineKeyboardButton('❌ ᴄʟᴏsᴇ', callback_data='close_data', style=ButtonStyle.DANGER)
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await message.reply_text(
        text=Texts.HELP2_TXT,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

@Client.on_message(filters.private & filters.command("files"))
async def list_user_files(client, message: Message):
    user_id = message.from_user.id
    files = await store.files.find({"user_id": user_id}).to_list(length=100)
    if not files:
        return await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
    page = 1
    per_page = 7
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(files) + per_page - 1) // per_page
    btns = []
    for f in files[start:end]:
        name = f["file_name"][:40]
        btns.append([InlineKeyboardButton(name, callback_data=f"sendfile_{f['file_id']}", style=ButtonStyle.PRIMARY)])
    nav_btns = []
    if page < total_pages:
        nav_btns.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"filespage_{page + 1}", style=ButtonStyle.SUCCESS))
    nav_btns.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close_data", style=ButtonStyle.DANGER))
    btns.append(nav_btns)
    await message.reply_photo(photo=FILE_PIC,
        caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(btns)
    )

@Client.on_message(filters.private & filters.command("del_files"))
async def delete_files_list(client, message):
    user_id = message.from_user.id
    files = await store.files.find({"user_id": user_id}).to_list(length=100)
    if not files:
        return await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
    page = 1
    per_page = 7
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(files) + per_page - 1) // per_page
    btns = []
    for f in files[start:end]:
        name = f["file_name"][:40]
        btns.append([InlineKeyboardButton(name, callback_data=f"deletefile_{f['file_id']}", style=ButtonStyle.DANGER)])
    nav_btns = []
    if page < total_pages:
        nav_btns.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"delfilespage_{page + 1}", style=ButtonStyle.SUCCESS))
    nav_btns.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close_data", style=ButtonStyle.DANGER))
    btns.append(nav_btns)
    await message.reply_photo(photo=FILE_PIC,
        caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(btns)
   )
    
