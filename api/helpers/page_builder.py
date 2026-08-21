import jinja2
import urllib.parse
import aiofiles
import logging
from config import URL, BIN_CHANNEL
from helpers import app_state, humanbytes
from api.client import app_bot
from api.helpers.file_meta import resolve_file_id
from api.server.errors import InvalidHash


async def build_page(id, secure_hash):
    file_data = await resolve_file_id(app_bot, int(BIN_CHANNEL), int(id))

    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message ID {id}")
        raise InvalidHash

    raw_file_name = file_data.file_name or f"File_{id}"
    file_name = raw_file_name.replace("_", " ").replace(".", " ")
    safe_quoted_name = urllib.parse.quote_plus(str(raw_file_name))
    src = urllib.parse.urljoin(URL, f"{id}/{safe_quoted_name}?hash={secure_hash}")

    tag = file_data.mime_type.split("/")[0].strip() if file_data.mime_type else ""
    file_size = humanbytes(file_data.file_size)

    template_file = (
        "api/template/player.html"
        if tag in ("video", "audio")
        else "api/template/download.html"
    )

    async with aiofiles.open(template_file, mode="r") as f:
        template = jinja2.Template(await f.read())

    file_get_link = f"https://t.me/{app_state.U_NAME}?start=file_{id}"

    return template.render(
        file_name=file_name,
        file_url=src,
        file_size=file_size,
        file_get=file_get_link,
        file_unique_id=file_data.unique_id,
        mime_type=file_data.mime_type or "video/mp4",
    )
