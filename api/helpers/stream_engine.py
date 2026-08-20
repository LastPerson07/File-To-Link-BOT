import asyncio
import logging
from typing import AsyncIterator, Dict

from pyrogram import Client, raw, utils
from pyrogram.errors import FloodWait
from pyrogram.file_id import FileId, FileType, ThumbnailSource
from pyrogram.session import Session

from settings import BIN_CHANNEL
from api.client import active_loads
from api.server.errors import FileNotFound
from .file_meta import resolve_file_id

PREFETCH = 8


class FileStreamer:
    def __init__(self, client: Client):
        self.clean_timer = 30 * 60
        self.client = client
        self.cached_file_ids: Dict[int, FileId] = {}
        try:
            asyncio.create_task(self.clean_cache())
        except RuntimeError:
            pass

    async def get_file_properties(self, id: int) -> FileId:
        if id not in self.cached_file_ids:
            await self.generate_file_properties(id)
        return self.cached_file_ids[id]

    async def generate_file_properties(self, id: int) -> FileId:
        file_id = await resolve_file_id(self.client, BIN_CHANNEL, id)
        if not file_id:
            raise FileNotFound
        self.cached_file_ids[id] = file_id
        return file_id

    async def open_media_session(self, client: Client, file_id: FileId) -> Session:
        return await client.get_session(file_id.dc_id, is_media=True)

    @staticmethod
    async def get_location(file_id: FileId):
        file_type = file_id.file_type
        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id, access_hash=file_id.chat_access_hash
                )
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )
            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        return location

    async def stream_file(
        self,
        file_id: FileId,
        index: int,
        offset: int,
        first_part_cut: int,
        last_part_cut: int,
        part_count: int,
        chunk_size: int,
    ) -> AsyncIterator[bytes]:
        client = self.client
        active_loads[index] += 1
        try:
            media_session = await self.open_media_session(client, file_id)
            location = await self.get_location(file_id)
            queue: asyncio.Queue = asyncio.Queue(maxsize=PREFETCH)
            stop = asyncio.Event()

            async def producer():
                try:
                    off = offset
                    for part in range(1, part_count + 1):
                        if stop.is_set():
                            break
                        while True:
                            try:
                                r = await media_session.send(
                                    raw.functions.upload.GetFile(
                                        location=location, offset=off, limit=chunk_size
                                    )
                                )
                                break
                            except FloodWait as e:
                                await asyncio.sleep(e.value)
                        if not isinstance(r, raw.types.upload.File):
                            break
                        await queue.put((part, r.bytes))
                        off += chunk_size
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logging.error(f"Stream producer error: {e}")
                finally:
                    while True:
                        try:
                            queue.put_nowait(None)
                            break
                        except asyncio.QueueFull:
                            try:
                                queue.get_nowait()
                            except asyncio.QueueEmpty:
                                break

            producer_task = asyncio.create_task(producer())
            try:
                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    part, chunk = item
                    if not chunk:
                        break
                    if part_count == 1:
                        yield chunk[first_part_cut:last_part_cut]
                    elif part == 1:
                        yield chunk[first_part_cut:]
                    elif part == part_count:
                        yield chunk[:last_part_cut]
                    else:
                        yield chunk
            finally:
                stop.set()
                while True:
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                try:
                    await asyncio.wait_for(producer_task, timeout=20)
                except (asyncio.TimeoutError, asyncio.CancelledError, Exception):
                    producer_task.cancel()
                    try:
                        await producer_task
                    except (asyncio.CancelledError, Exception):
                        pass
        except (TimeoutError, AttributeError) as e:
            logging.error(f"Error yielding file: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in stream_file: {e}")
        finally:
            active_loads[index] -= 1

    async def clean_cache(self) -> None:
        while True:
            await asyncio.sleep(self.clean_timer)
            self.cached_file_ids.clear()
