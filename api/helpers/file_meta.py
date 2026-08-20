from pyrogram import Client
from typing import Any, Optional
import logging
from pyrogram.types import Message
from pyrogram.file_id import FileId
from pyrogram.raw.types.messages import Messages
from api.server.errors import FileNotFound
from database.store import store

def parse_file_id(message: "Message") -> Optional[FileId]:
    media = get_media_from_message(message)
    if media:
        return FileId.decode(media.file_id)

def parse_file_unique_id(message: "Messages") -> Optional[str]:
    media = get_media_from_message(message)
    if media:
        return media.file_unique_id

async def resolve_file_id(client: Client, chat_id: int, id: int) -> Optional[FileId]:
    cached = await store.get_cached_file_meta(id)
    if cached:
        try:
            file_id = FileId.decode(cached["file_id_str"])
            file_id.file_size = cached.get("file_size", 0)
            file_id.mime_type = cached.get("mime_type", "")
            file_id.file_name = cached.get("file_name", "")
            file_id.unique_id = cached.get("unique_id", "")
            logging.debug(f"Using cached file metadata for message ID {id}")
            return file_id
        except Exception as e:
            logging.warning(f"Failed to decode cached file_id for {id}: {e}")

    message = await client.get_messages(chat_id, id)
    if message.empty:
        raise FileNotFound
    media = get_media_from_message(message)
    if not media:
        raise FileNotFound
    file_unique_id = parse_file_unique_id(message)
    file_id = parse_file_id(message)
    setattr(file_id, "file_size", getattr(media, "file_size", 0))
    setattr(file_id, "mime_type", getattr(media, "mime_type", ""))
    setattr(file_id, "file_name", getattr(media, "file_name", ""))
    setattr(file_id, "unique_id", file_unique_id)

    await store.set_cached_file_meta(
        id,
        {
            "file_id_str": file_id.encode(),
            "unique_id": file_unique_id,
            "file_name": getattr(media, "file_name", ""),
            "mime_type": getattr(media, "mime_type", ""),
            "file_size": getattr(media, "file_size", 0),
        },
    )
    return file_id

def get_media_from_message(message: "Message") -> Any:
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )
    for attr in media_types:
        media = getattr(message, attr, None)
        if media:
            return media

def get_hash(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6]
