class Texts(object):
    START_TXT = """<b>Hey {}! 👋

I'm a File to Link Generator Bot.

Send me any file or video and I'll give you a direct download & stream link.

<blockquote>➤ Add me as admin in your channel and I'll auto-generate links for every file you post.</blockquote>

<blockquote>DEV<a href='https://t.me/DmOwner'>Ⓜ️ark</a></blockquote></b>"""

    RESTART_TXT = """<b>Bot Restarted ✅

<blockquote>📅 Date: <code>{}</code>
⏰ Time: <code>{}</code>
🌐 Timezone: <code>Asia/Kolkata</code>
🛠️ Version: <code>{}</code></blockquote></b>"""

    HELP_TXT = """<b>How to use this bot?

<blockquote>Just send me any file and I'll return a download & stream link. You can also add me as admin in your channel to auto-generate links.</blockquote>
"""

    ADMIN_CMD_TXT = """<b>Admin Commands:

<blockquote>/users — Total users count
/status — Bot status & client loads
/stats — Full bot statistics
/speedtest — Server speedtest
/shell — Run shell command
/restart — Restart the bot

/ban — Ban a user or channel
/unban — Unban a user or channel
/blocked — List blocked users/channels

/broadcast — Broadcast to all users (reply)
/pin_broadcast — Broadcast + pin (reply)

/delfile — Delete a user's files
/file_stats — File statistics report</blockquote></b>"""

    HELP2_TXT = """<b> Help

<blockquote>• Send any file → get a download & stream link
- Add bot as admin in your channel → links auto-generate
- Links are permanent and never expire
- Unlimited file size supported</blockquote>

<blockquote>⚠️WE also <b>support</b> Inappropriate or adult content.</blockquote>

<blockquote>📮 Support: @THEUPDATEDGUYSGROUP
🔔 Channel: @THEUPDATEDGUYSz</blockquote>

<u><i>Report bugs to <a href='https://t.me/DmOwner'>Developer</a></i></u></b>"""

    LOG_TEXT = """#NewUser
<blockquote>🆔 ID: <code>{}</code>
👤 Name: {}</blockquote>"""

    BOT_STATS_TEXT = """<b>📊 ᴀᴅᴠᴀɴᴄᴇᴅ ʙᴏᴛ sᴛᴀᴛs</b>

<blockquote>👥 ᴜsᴇʀ ᴅᴀᴛᴀ
• ᴛᴏᴛᴀʟ ᴜsᴇʀs : <code>{total_users}</code>
• ʙʟᴏᴄᴋᴇᴅ      : <code>{blocked_users}</code></blockquote>

<blockquote>🗂️ ᴄᴏɴᴛᴇɴᴛ ᴅᴀᴛᴀ
• ᴛᴏᴛᴀʟ ꜰɪʟᴇs      : <code>{total_files}</code>
• ʙʟᴏᴄᴋᴇᴅ ᴄʜᴀɴɴᴇʟs : <code>{blocked_channels}</code></blockquote>

<blockquote>🖥️ sᴇʀᴠᴇʀ sᴛᴀᴛᴜs
• ᴄᴘᴜ ᴜsᴀɢᴇ : <code>{cpu_usage}%</code>
• ʀᴀᴍ ᴜsᴀɢᴇ : <code>{ram_usage}%</code>
• ᴅɪsᴋ ᴛᴏᴛᴀʟ : <code>{total}</code>
• ᴜsᴇᴅ sᴘᴀᴄᴇ : <code>{used}</code>
• ꜰʀᴇᴇ sᴘᴀᴄᴇ : <code>{free}</code></blockquote>"""

    ABOUT_TXT = """<b>About This Bot

<blockquote>🤖 Name: {}
👦 Developer: <a href='https://t.me/DmOwner'>Ⓜ️ark</a>
🔔 Channel: <a href='https://t.me/THEUPDATEDGUYS'>THE UPDATED GUYS 😎</a>
⏲️ Uptime: {}
🗣️ Language: Python
🗒️ Version: {} Stable</blockquote></b>"""

    AUTH_TXT = """<b>Hey {}!

<blockquote>To use this bot, please join our updates channel first.

Click "Join Channel" → then "Try Again".</blockquote></b>"""

    CAPTION_TXT = """<b>✅ Link Generated!

<blockquote>📧 File: <a href='https://t.me/THEUPDATEDGUYS'>{}</a>
📦 Size: {}</blockquote>

<blockquote>🖥 Stream: {}
📥 Download: {}</blockquote>

<blockquote>🚸 Link won't expire unless deleted.</blockquote></b>"""
