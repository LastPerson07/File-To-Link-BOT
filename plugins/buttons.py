import html
from texts import Texts
from database.store import store
from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from settings import ADMINS, URL, CHANNEL, BIN_CHANNEL, FILE_CAPTION
from api.helpers.file_meta import get_hash
from helpers import app_state
from api.helpers import about_text
from keyboards import ButtonStyle, _start_markup

PER_PAGE = 7


def _paged_markup(files, page, mode):
    total_pages = (len(files) + PER_PAGE - 1) // PER_PAGE
    prefix = "filespage" if mode == "files" else "delfilespage"
    is_files = mode == "files"
    btns = []
    for f in files[(page - 1) * PER_PAGE: page * PER_PAGE]:
        name = f["file_name"][:40]
        callback = f"sendfile_{f['file_id']}" if is_files else f"deletefile_{f['file_id']}"
        style = ButtonStyle.PRIMARY if is_files else ButtonStyle.DANGER
        btns.append([InlineKeyboardButton(name, callback_data=callback, style=style)])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data=f"{prefix}_{page - 1}", style=ButtonStyle.PRIMARY))
    if page < total_pages:
        nav.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"{prefix}_{page + 1}", style=ButtonStyle.SUCCESS))
    nav.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close_data", style=ButtonStyle.DANGER))
    btns.append(nav)
    return InlineKeyboardMarkup(btns)


async def _edit_files_page(query, page, mode):
    files = await store.files.find({"user_id": query.from_user.id}).to_list(length=100)
    total_pages = (len(files) + PER_PAGE - 1) // PER_PAGE
    if not files or page < 1 or page > total_pages:
        return await query.answer("⚠️ Nᴏ ᴍᴏʀᴇ ғɪʟᴇꜱ.", show_alert=True)
    await query.message.edit_caption(
        caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
        reply_markup=_paged_markup(files, page, mode),
    )
    return await query.answer()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
        await query.answer()

    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('💻 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ', url='https://github.com/LastPerson07/File-To-Link-BOT', style=ButtonStyle.PRIMARY)
        ], [
            InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start', style=ButtonStyle.SUCCESS),
            InlineKeyboardButton('❌ ᴄʟᴏsᴇ', callback_data='close_data', style=ButtonStyle.DANGER)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=about_text(app_state.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer()

    elif query.data == "start":
        await query.message.edit_text(
            text=Texts.START_TXT.format(query.from_user.mention),
            reply_markup=_start_markup(),
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer()

    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('👮 ᴀᴅᴍɪɴ', callback_data='admincmd', style=ButtonStyle.DANGER)
        ], [
            InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start', style=ButtonStyle.SUCCESS),
            InlineKeyboardButton('❌ ᴄʟᴏsᴇ', callback_data='close_data', style=ButtonStyle.DANGER)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=Texts.HELP_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer()

    elif query.data == "admincmd":
        if query.from_user.id not in ADMINS:
            return await query.answer('This Feature Is Only For Admins !', show_alert=True)
        buttons = [[
            InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start', style=ButtonStyle.SUCCESS)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=Texts.ADMIN_CMD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML,
        )
        await query.answer()

    elif query.data.startswith("stream"):
        try:
            msg_id = int(query.data.split('#', 1)[1])
            original_msg = await client.get_messages(int(BIN_CHANNEL), msg_id)
            if not original_msg or original_msg.empty:
                return await query.answer("❌ File not found.", show_alert=True)
            online = f"{URL}watch/{original_msg.id}?hash={get_hash(original_msg)}"
            download = f"{URL}{original_msg.id}?hash={get_hash(original_msg)}"
            btn = [[
                InlineKeyboardButton("▶️ ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ", url=online, style=ButtonStyle.SUCCESS),
                InlineKeyboardButton("⬇️ ꜰᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ", url=download, style=ButtonStyle.SUCCESS)
            ], [
                InlineKeyboardButton('❌ ᴄʟᴏsᴇ', callback_data='close_data', style=ButtonStyle.DANGER)
            ]]
            await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
            await query.answer()
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)

    elif query.data.startswith("filespage_"):
        page = int(query.data.split("_")[1])
        return await _edit_files_page(query, page, mode="files")

    elif query.data.startswith("delfilespage_"):
        page = int(query.data.split("_")[1])
        return await _edit_files_page(query, page, mode="delete")

    elif query.data.startswith("sendfile_"):
        file_id = int(query.data.split("_")[1])
        user_id = query.from_user.id
        file_data = await store.files.find_one({"file_id": file_id, "user_id": user_id})
        if not file_data:
            return await query.answer("⚠️ Nᴏ ᴍᴏʀᴇ ғɪʟᴇꜱ.", show_alert=True)
        try:
            original_message = await client.get_messages(BIN_CHANNEL, file_id)
            media = original_message.document or original_message.video or original_message.audio
            caption = None
            if media:
                file_name = getattr(media, "file_name", "Unnamed") or "Unnamed"
                caption = FILE_CAPTION.format(CHANNEL, html.escape(file_name))
            await client.copy_message(
                chat_id=user_id,
                from_chat_id=BIN_CHANNEL,
                message_id=file_id,
                caption=caption
            )
            return await query.answer()
        except Exception:
            return await query.answer("⚠️ Failed to send file.", show_alert=True)

    elif query.data.startswith("deletefile_"):
        file_msg_id = int(query.data.split("_")[1])
        user_id = query.from_user.id
        file_data = await store.files.find_one({"file_id": file_msg_id})
        if not file_data:
            return await query.answer("❌ Fɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏʀ ᴀʟʀᴇᴀᴅʏ ᴅᴇʟᴇᴛᴇᴅ.", show_alert=True)
        if file_data["user_id"] != user_id:
            return await query.answer("⚠️ Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪꜱ ꜰɪʟᴇ!", show_alert=True)
        await store.files.delete_one({"file_id": file_msg_id})
        try:
            await client.delete_messages(BIN_CHANNEL, file_msg_id)
        except Exception:
            pass
        await query.answer("✅ Fɪʟᴇ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ!", show_alert=True)
        await query.message.edit_text("🗑️ Fɪʟᴇ ʜᴀꜱ ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ.")