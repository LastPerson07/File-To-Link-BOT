import os
import sys
import shutil
import logging
import psutil
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from database.store import store
from settings import ADMINS
from texts import Texts
from helpers import humanbytes

@Client.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def bot_stats(client: Client, message: Message):
    status_msg = await message.reply_text("🔄 **Fetching Stats...**", quote=True)
    try:
        total_users = await store.total_users_count()
        blocked_users = await store.total_blocked_count()
        blocked_channels = await store.total_blocked_channels_count()
        total_files = await store.files.count_documents({})
        total, used, free = shutil.disk_usage(".")
        total = humanbytes(total)
        used = humanbytes(used)
        free = humanbytes(free)
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        await status_msg.edit(Texts.BOT_STATS_TEXT.format(total_users=total_users, blocked_users=blocked_users, total_files=total_files, blocked_channels=blocked_channels, cpu_usage=cpu_usage, ram_usage=ram_usage, total=total, used=used, free=free), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await status_msg.edit(f"❌ **Error Fetching Stats:**\n`{e}`")

@Client.on_message(filters.command("restart") & filters.private & filters.user(ADMINS))
async def restart_bot(client: Client, message: Message):
    try:
        msg = await message.reply_text("<i>♻️ Restarting the bot, please wait...</i>")
        await asyncio.sleep(2)
        await msg.edit("<i>✅ System Restart Initiated...\nI will be back in few seconds!</i>")
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        logging.error(f"Restart Error: {e}")
        await message.reply_text(f"❌ Error while restarting: `{e}`")

