import time
from aiohttp import web
import re
import math
import logging
import secrets
import mimetypes
from aiohttp.http_exceptions import BadStatusLine
from api.client import tg_clients, active_loads
from api.client.launcher import pick_client
from api.server.errors import FileNotFound, InvalidHash
from api.helpers.stream_engine import FileStreamer
from api.helpers.page_builder import build_page
from settings import MULTI_CLIENT
from helpers import app_state, get_readable_time
from api.helpers import boot_time, __version__
from database.store import store

def _parse_id(path: str) -> int:
    return int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))


def _part_count(until_bytes: int, offset: int, chunk_size: int) -> int:
    return math.floor(until_bytes / chunk_size) - math.floor(offset / chunk_size) + 1


routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.json_response({
        "server_status": "running",
        "uptime": get_readable_time(time.time() - boot_time),
        "telegram_bot": "@" + app_state.U_NAME,
        "connected_bots": len(tg_clients),
        "loads": {
            "bot" + str(i + 1): load
            for i, (_, load) in enumerate(
                sorted(active_loads.items(), key=lambda x: x[1], reverse=True)
            )
        },
        "version": __version__,
    })

@routes.get("/health", allow_head=True)
async def health_route_handler(_):
    db_ok = False
    try:
        await store.users.database.command("ping")
        db_ok = True
    except Exception as e:
        logging.warning(f"Health check DB ping failed: {e}")
    return web.json_response({
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "uptime": get_readable_time(time.time() - boot_time),
        "connected_bots": len(tg_clients),
    })

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        id = _parse_id(path)
        secure_hash = request.rel_url.query.get("hash")
        return web.Response(
            text=await build_page(id, secure_hash), content_type="text/html"
        )
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FileNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        return web.Response(status=400, text="Connection Error")
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))


@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        id = _parse_id(path)
        secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FileNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        return web.Response(status=400, text="Connection Error")
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

class_cache = {}


async def media_streamer(request: web.Request, id: int, secure_hash: str):
    range_header = request.headers.get("Range")

    index = pick_client()
    faster_client = tg_clients[index]

    if MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached FileStreamer object for client {index}")
    else:
        logging.debug(f"Creating new FileStreamer object for client {index}")
        tg_connect = FileStreamer(faster_client)
        class_cache[faster_client] = tg_connect
    logging.debug("before calling get_file_properties")
    file_id = await tg_connect.get_file_properties(id)
    logging.debug("after calling get_file_properties")

    if file_id.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with ID {id}")
        raise InvalidHash

    file_size = file_id.file_size

    if range_header:
        try:
            from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
            from_bytes = int(from_bytes)
            until_bytes = int(until_bytes) if until_bytes else file_size - 1
        except ValueError:
            from_bytes, until_bytes = 0, file_size - 1
    else:
        from_bytes, until_bytes = 0, file_size - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = _part_count(until_bytes, offset, chunk_size)
    body = tg_connect.stream_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )

    mime_type = file_id.mime_type
    file_name = file_id.file_name
    disposition = "attachment"

    if mime_type:
        if not file_name:
            try:
                file_name = f"{secrets.token_hex(2)}.{mime_type.split('/')[1]}"
            except (IndexError, AttributeError):
                file_name = f"{secrets.token_hex(2)}.unknown"
    else:
        if file_name:
            mime_type = mimetypes.guess_type(file_id.file_name)[0] or "application/octet-stream"
        else:
            mime_type = "application/octet-stream"
            file_name = f"{secrets.token_hex(2)}.unknown"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        },
)
