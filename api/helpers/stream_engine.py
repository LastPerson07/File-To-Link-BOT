import asyncio
import logging
from typing import AsyncIterator, Dict

from pyrogram import Client, raw, utils
from pyrogram.errors import FloodWait
from pyrogram.file_id import FileId, FileType, ThumbnailSource

from config import BIN_CHANNEL
from api.client import active_loads
from api.server.errors import FileNotFound
from .file_meta import resolve_file_id

log = logging.getLogger(__name__)

CONCURRENT_FETCHES = 6


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

    async def open_media_session(self, client: Client, file_id: FileId):
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
        active_loads[index] += 1
        tasks = []
        try:
            media_session = await self.open_media_session(self.client, file_id)
            location = await self.get_location(file_id)

            sem = asyncio.Semaphore(CONCURRENT_FETCHES)

            async def fetch_part(part: int) -> bytes:
                part_offset = offset + (part - 1) * chunk_size
                async with sem:
                    while True:
                        try:
                            r = await media_session.send(
                                raw.functions.upload.GetFile(
                                    location=location,
                                    offset=part_offset,
                                    limit=chunk_size,
                                )
                            )
                            return r.bytes if isinstance(r, raw.types.upload.File) else b""
                        except FloodWait as e:
                            await asyncio.sleep(e.value)

            tasks = [asyncio.ensure_future(fetch_part(p)) for p in range(1, part_count + 1)]

            for part, task in enumerate(tasks, start=1):
                chunk = await task
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
        except (TimeoutError, AttributeError) as e:
            log.error(f"Error yielding file: {e}")
        except Exception as e:
            log.error(f"Unexpected error in stream_file: {e}")
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            active_loads[index] -= 1

    async def clean_cache(self) -> None:
        while True:
            await asyncio.sleep(self.clean_timer)
            self.cached_file_ids.clear()
