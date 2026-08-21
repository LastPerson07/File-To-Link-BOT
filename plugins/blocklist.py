from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS
from database.store import store

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: `/ban user_id_or_channel_id [reason]`", quote=True)
    try:
        target_id = int(message.command[1])
        reason = " ".join(message.command[2:]) or "No reason"

        if str(target_id).startswith("-100"):
            await store.block_channel(target_id, reason)
            await message.reply(f"🚫 Channel `{target_id}` banned.\n📝 Reason: `{reason}`", quote=True)
            try:
                await client.send_message(target_id, f"🚫 This channel is banned.\nReason: `{reason}`")
            except Exception: pass
        else:
            await store.block_user(target_id, reason)
            await message.reply(f"🚫 User `{target_id}` banned.\n📝 Reason: `{reason}`", quote=True)
            try:
                await client.send_message(target_id, f"🚫 You are banned.\nReason: `{reason}`")
            except Exception: pass

    except Exception as e:
        await message.reply(f"❌ Error banning: `{e}`", quote=True)

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: `/unban user_id_or_channel_id`", quote=True)
    try:
        target_id = int(message.command[1])

        if str(target_id).startswith("-100"):
            await store.unblock_channel(target_id)
            await message.reply(f"✅ Channel `{target_id}` unbanned.", quote=True)
        else:
            await store.unblock_user(target_id)
            await message.reply(f"✅ User `{target_id}` unbanned.", quote=True)
            try:
                await client.send_message(target_id, "✅ You are unbanned.")
            except Exception: pass

    except Exception as e:
        await message.reply(f"❌ Error unbanning: `{e}`", quote=True)

@Client.on_message(filters.command("blocked") & filters.user(ADMINS))
async def list_blocked_users(client, message: Message):
    text = "**🚫 Blocked Users:**\n\n"
    async for user in await store.get_all_blocked_users():
        uid = user.get("user_id")
        reason = user.get("reason", "No reason")
        blocked_at = user.get("blocked_at")
        time_str = blocked_at.strftime("%Y-%m-%d %H:%M") if blocked_at else "Unknown"
        text += f"• 👤 `{uid}` - `{reason}` - `{time_str}`\n"

    async for ch in await store.get_all_blocked_channels():
        cid = ch.get("channel_id")
        reason = ch.get("reason", "No reason")
        blocked_at = ch.get("blocked_at")
        time_str = blocked_at.strftime("%Y-%m-%d %H:%M") if blocked_at else "Unknown"
        text += f"• 📣 `{cid}` - `{reason}` - `{time_str}`\n"

    if text.strip() == "**🚫 Blocked Users:**":
        text = "✅ No blocked users or channels."
    await message.reply(text)
