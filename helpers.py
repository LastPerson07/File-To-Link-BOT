import asyncio
import logging
import aiohttp
from config import PING_INTERVAL, URL

logger = logging.getLogger(__name__)


class app_state:
    U_NAME = None
    B_NAME = None


async def keep_alive():
    while True:
        await asyncio.sleep(PING_INTERVAL)
        try:
            if not URL:
                logger.warning("URL is empty, cannot keep the server alive.")
                continue

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(URL) as resp:
                    logger.info(f"Keep-alive ping returned {resp.status}")
        except asyncio.TimeoutError:
            logger.warning("Keep-alive ping timed out.")
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}", exc_info=True)


def humanbytes(size: int) -> str:
    if size is None:
        return "0 B"
    power = 2 ** 10
    n = 0
    labels = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size >= power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {labels[n]}"


def get_readable_time(seconds: int) -> str:
    if not seconds:
        return "0s"

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days:
        parts.append(f"{int(days)} days")
    if hours:
        parts.append(f"{int(hours)}h")
    if minutes:
        parts.append(f"{int(minutes)}m")
    if seconds:
        parts.append(f"{int(seconds)}s")
    return ": ".join(parts)


async def cleanup_after_delay(message, delay: int = 600):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass
