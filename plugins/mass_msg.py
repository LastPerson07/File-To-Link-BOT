from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

import time
import asyncio
import logging

from database.store import store
from config import ADMINS
from keyboards import ButtonStyle
from helpers import get_readable_time

lock = asyncio.Lock()
_broadcast_cancel = False

async def _send_one(bot, user_id, message, is_pin):
    try:
        m = await message.copy(chat_id=user_id)
        if is_pin:
            await m.pin(both_sides=True)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await _send_one(bot, user_id, message, is_pin)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        await store.delete_user(int(user_id))
        return False
    except Exception as e:
        logging.error(f"Error broadcasting to {user_id}: {e}")
        return False

async def _broadcast_chunk(bot, users, message, is_pin, status_msg, total_users, start_time):
    done = [0]
    success = [0]
    failed = [0]

    async def _send(user_id):
        if _broadcast_cancel:
            return
        ok = await _send_one(bot, int(user_id), message, is_pin)
        done[0] += 1
        if ok:
            success[0] += 1
        else:
            failed[0] += 1

        if done[0] % 20 == 0:
            btn = [[InlineKeyboardButton('CANCEL', callback_data='broadcast_cancel#users', style=ButtonStyle.DANGER)]]
            time_taken = get_readable_time(int(time.time() - start_time))
            try:
                await status_msg.edit(
                    f"📢 Broadcast in progress...\n\n"
                    f"Total Users: <code>{total_users}</code>\n"
                    f"Completed: <code>{done[0]}</code>\n"
                    f"Success: <code>{success[0]}</code>\n"
                    f"Failed: <code>{failed[0]}</code>\n"
                    f"Time: <code>{time_taken}</code>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception:
                pass

    await asyncio.gather(*[_send(u['id']) for u in users])
    return done[0], success[0], failed[0]

@Client.on_callback_query(filters.regex(r'^broadcast_cancel'))
async def broadcast_cancel(bot, query):
    global _broadcast_cancel
    _, ident = query.data.split("#")
    if ident == 'users':
        _broadcast_cancel = True
        await query.message.edit("Trying to cancel users broadcasting...")

async def process_broadcast(bot, message, is_pin: bool):
    global _broadcast_cancel
    if lock.locked():
        return await message.reply('Currently broadcast processing, Wait for complete.')

    await bot.send_message(chat_id=message.chat.id, text="Broadcast started...", reply_markup=ReplyKeyboardRemove())

    users = []
    async for user in await store.get_all_users():
        users.append(user)

    b_msg = message.reply_to_message
    b_sts = await message.reply_text(text='<b>Broadcasting your messages to users ⌛️</b>')

    start_time = time.time()
    total_users = len(users)
    done = 0
    success = 0
    failed = 0

    async with lock:
        _broadcast_cancel = False
        chunk_size = 500
        for i in range(0, total_users, chunk_size):
            if _broadcast_cancel:
                _broadcast_cancel = False
                time_taken = get_readable_time(int(time.time() - start_time))
                await b_sts.edit(
                    f"❌ Users broadcast cancelled!\nCompleted in {time_taken}\n\n"
                    f"Total Users: <code>{total_users}</code>\n"
                    f"Completed: <code>{done}</code>\n"
                    f"Success: <code>{success}</code>\n"
                    f"Failed: <code>{failed}</code>"
                )
                return

            chunk = users[i:i + chunk_size]
            d, s, f = await _broadcast_chunk(bot, chunk, b_msg, is_pin, b_sts, total_users, start_time)
            done += d
            success += s
            failed += f

        time_taken = get_readable_time(int(time.time() - start_time))
        await b_sts.edit(
            f"✅ Users broadcast completed!\nCompleted in {time_taken}\n\n"
            f"Total Users: <code>{total_users}</code>\n"
            f"Completed: <code>{done}</code>\n"
            f"Success: <code>{success}</code>\n"
            f"Failed: <code>{failed}</code>"
        )

# Command: /broadcast (only send)
@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_only(bot, message):
    await process_broadcast(bot, message, is_pin=False)

# Command: /pin_broadcast (send + pin)
@Client.on_message(filters.command("pin_broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_with_pin(bot, message):
    await process_broadcast(bot, message, is_pin=True)
