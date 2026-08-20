import os
from pyrogram import Client, filters
from pyrogram.types import Message
from database.store import store
from settings import ADMINS

@Client.on_message(filters.command("delfile") & filters.user(ADMINS))
async def delete_user_files(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("⚠️ **Usage:** `/delfile [User_ID]`", quote=True)

    try:
        target_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ **Error:** User ID number hona chahiye!", quote=True)

    count = await store.files.count_documents({"user_id": target_id})

    if count == 0:
        return await message.reply_text(f"❌ User ID `{target_id}` ki database mein koi files nahi mili.", quote=True)

    status_msg = await message.reply_text(f"⏳ Deleting **{count}** files...", quote=True)

    await store.files.delete_many({"user_id": target_id})
    
    await status_msg.edit(f"✅ **Success!**\n\nUser ID `{target_id}` ki **{count} files** delete kar di gayi hain.")


@Client.on_message(filters.command("file_stats") & filters.user(ADMINS))
async def user_file_stats_txt(client: Client, message: Message):

    status_msg = await message.reply_text("🔄 **Generating Statistics File... Wait.**", quote=True)

    try:
        pipeline = [
            {"$group": {"_id": "$user_id", "total_files": {"$sum": 1}}},
            {"$sort": {"total_files": -1}}
        ]
        results = await store.files.aggregate(pipeline).to_list(length=None)

        if not results:
            return await status_msg.edit("❌ UserStore is empty. No files found.")

        file_path = "User_File_Stats.txt"

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("=========================================\n")
            file.write("         USER FILE STATISTICS           \n")
            file.write(f"     Total Uploaders: {len(results)}\n")
            file.write("=========================================\n\n")
            file.write(f"{'Rank':<5} | {'User ID':<15} | {'Files Count'}\n")
            file.write("-----------------------------------------\n")

            for i, user in enumerate(results, start=1):
                user_id = user["_id"]
                total = user["total_files"]
                file.write(f"{i:<5} | {str(user_id):<15} | {total}\n")

        await message.reply_document(
            document=file_path,
            caption=f"📊 **File Stats Generated!**\n\nTotal Users with files: `{len(results)}`",
            file_name="User_File_Stats.txt"
        )

        await status_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")
        if os.path.exists("User_File_Stats.txt"):
            os.remove("User_File_Stats.txt")

