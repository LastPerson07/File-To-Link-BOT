import time
import logging
from typing import Optional, Dict, Any

import aiohttp

logger = logging.getLogger(__name__)

_DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes={}"
_UPLOAD_URL = "https://speed.cloudflare.com/__up"
_PING_URL = "https://speed.cloudflare.com/__down?bytes=0"

_DOWNLOAD_BYTES = 25_000_000   # 25 MB
_UPLOAD_BYTES = 10_000_000     # 10 MB


async def run_speedtest() -> Optional[Dict[str, Any]]:
    try:
        timeout = aiohttp.ClientTimeout(total=90)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            ping_ms = await _measure_ping(session)
            download_mbps = await _measure_download(session)
            upload_mbps = await _measure_upload(session)
    except Exception as e:
        logger.error(f"Speedtest failed: {e}", exc_info=True)
        return None

    return {
        "ping": ping_ms,
        "download_mbps": download_mbps,
        "upload_mbps": upload_mbps,
        "server": {"name": "Cloudflare", "country": "Global"},
        "client": {"isp": "Cloudflare Edge"},
    }


async def _measure_ping(session: aiohttp.ClientSession) -> float:
    best = None
    for _ in range(3):
        start = time.perf_counter()
        async with session.get(_PING_URL) as resp:
            await resp.read()
        elapsed = (time.perf_counter() - start) * 1000
        best = elapsed if best is None else min(best, elapsed)
    return best or 0.0


async def _measure_download(session: aiohttp.ClientSession) -> float:
    total = 0
    start = time.perf_counter()
    async with session.get(_DOWNLOAD_URL.format(_DOWNLOAD_BYTES)) as resp:
        async for chunk in resp.content.iter_chunked(64 * 1024):
            total += len(chunk)
    elapsed = time.perf_counter() - start
    return (total * 8) / elapsed / 1_000_000 if elapsed > 0 else 0.0


async def _measure_upload(session: aiohttp.ClientSession) -> float:
    payload = b"0" * _UPLOAD_BYTES
    start = time.perf_counter()
    async with session.post(_UPLOAD_URL, data=payload) as resp:
        await resp.read()
    elapsed = time.perf_counter() - start
    return (_UPLOAD_BYTES * 8) / elapsed / 1_000_000 if elapsed > 0 else 0.0
