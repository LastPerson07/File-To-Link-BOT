import asyncio
import html
import time
from io import BytesIO

from pyrogram import Client, filters
from pyrogram.file_id import FileId

from api.helpers import boot_time, __version__
from api.helpers.speedtest import run_speedtest
from api.client import tg_clients, active_loads
from database.store import store
from helpers import get_readable_time, humanbytes
from config import ADMINS

ADMIN = filters.user(ADMINS)


def _fmt(value, decimals=2):
    return f"{float(value):.{decimals}f}"


@Client.on_message(filters.command("users") & ADMIN)
async def users_command(client, message):
    try:
        total = await store.total_users_count()
        await message.reply_text(f"👥 **Total Users:** `{total}`", quote=True)
    except Exception as e:
        await message.reply_text(f"❌ Error: `{e}`", quote=True)


@Client.on_message(filters.command("status") & ADMIN)
async def status_command(client, message):
    try:
        uptime = get_readable_time(int(time.time() - boot_time))
        lines = [f"🔹 Client {cid}: `{load}`" for cid, load in sorted(active_loads.items())]
        workload = "\n".join(lines) if lines else "🔹 No clients"
        await message.reply_text(
            f"📊 **Bot Status**\n\n"
            f"⏱️ Uptime: `{uptime}`\n"
            f"🤖 Active bots: `{len(tg_clients)}`\n"
            f"📦 Version: `{__version__}`\n\n{workload}",
            quote=True,
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: `{e}`", quote=True)


@Client.on_message(filters.command("shell") & ADMIN)
async def shell_command(client, message):
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: /shell <command>")
    command = " ".join(message.command[1:])
    status_msg = await message.reply_text(
        f"⚙️ Executing:\n<code>{html.escape(command)}</code>"
    )
    try:
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = ""
        if stdout:
            output += html.escape(stdout.decode(errors="ignore"))
        if stderr:
            output += "\n[stderr]\n" + html.escape(stderr.decode(errors="ignore"))
        output = output.strip() or "✅ (no output)"
        await status_msg.delete()
        if len(output) > 4096:
            file = BytesIO(output.encode())
            file.name = "shell_output.txt"
            await message.reply_document(file, caption="Shell output")
        else:
            await message.reply_text(f"<pre>{output}</pre>", quote=True)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: `{html.escape(str(e))}`")


@Client.on_message(filters.command("speedtest") & ADMIN)
async def speedtest_command(client, message):
    status_msg = await message.reply_text("⚡ Running speedtest...", quote=True)
    try:
        result = await run_speedtest()
        if result is None:
            return await status_msg.edit_text("❌ Speedtest failed.")
        s, c = result["server"], result["client"]
        text = (
            f"⚡ **Speedtest Result**\n\n"
            f"⬇️ Download: `{_fmt(result['download_mbps'])} Mbps`\n"
            f"⬆️ Upload: `{_fmt(result['upload_mbps'])} Mbps`\n"
            f"📶 Ping: `{_fmt(result['ping'])} ms`\n\n"
            f"🖥️ Server: `{s['name']} ({s['country']})`\n"
            f"🌐 ISP: `{c['isp']}`"
        )
        await status_msg.edit_text(text)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: `{e}`")


@Client.on_message(filters.command("dc") & filters.user(ADMINS))
async def dc_command(client, message):
    args = message.text.strip().split(maxsplit=1)

    if len(args) > 1:
        qry = args[1].strip()
        try:
            if qry.startswith("@"):
                user = await client.get_users(qry)
            elif qry.isdigit():
                user = await client.get_users(int(qry))
            else:
                user = None
        except Exception:
            user = None
        if user:
            dc = user.dc_id if user.dc_id is not None else "Unknown"
            return await message.reply_text(
                f"👤 **User:** {user.mention}\n🆔 ID: `{user.id}`\n🌐 DC: `{dc}`", quote=True
            )
        return await message.reply_text("❌ User not found.", quote=True)

    if message.reply_to_message and message.reply_to_message.media:
        ref = message.reply_to_message
        media = ref.document or ref.video or ref.audio or ref.photo or ref.animation
        dc = "Unknown"
        if media and getattr(media, "file_id", None):
            try:
                dc = FileId.decode(media.file_id).dc_id
            except Exception:
                pass
        name = getattr(media, "file_name", None) or "File"
        size = humanbytes(getattr(media, "file_size", 0) or 0)
        return await message.reply_text(
            f"📁 **File:** `{name}`\n📦 Size: `{size}`\n🌐 DC: `{dc}`", quote=True
        )

    if message.from_user:
        user = message.from_user
        dc = user.dc_id if user.dc_id is not None else "Unknown"
        return await message.reply_text(
            f"👤 **User:** {user.mention}\n🆔 ID: `{user.id}`\n🌐 DC: `{dc}`", quote=True
        )

    await message.reply_text("⚠️ Usage: `/dc` (reply to file) or `/dc @username`", quote=True)
