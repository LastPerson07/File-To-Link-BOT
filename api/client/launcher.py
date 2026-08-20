import asyncio
import logging
from typing import Tuple, Optional

from pyrogram import Client

from . import tg_clients, active_loads, app_bot
from config import config

logger = logging.getLogger(__name__)


async def initialize_clients():
    """Start the main bot and any extra download bots concurrently."""
    tg_clients.clear()
    active_loads.clear()

    # Register the main bot as client 0
    tg_clients[0] = app_bot
    active_loads[0] = 0

    tokens = config.all_bot_tokens
    if len(tokens) <= 1:
        logger.info("No extra bot tokens configured, using the main bot only")
        return

    logger.info(f"Starting {len(tokens)} bot clients for multi-client streaming")

    async def start_client(client_id: int, token: str) -> Optional[Tuple[int, Client]]:
        if client_id > 1:
            await asyncio.sleep(2)
        try:
            logger.info(f"Starting download bot client {client_id}...")
            client = await Client(
                name=str(client_id),
                api_id=config.api_id,
                api_hash=config.api_hash,
                bot_token=token,
                sleep_threshold=config.sleep_threshold,
                no_updates=True,
                in_memory=True,
                workers=20,
            ).start()
            logger.info(f"Download bot client {client_id} ready")
            return client_id, client
        except Exception:
            logger.error(f"Failed to start download bot client {client_id}", exc_info=True)
            return None

    extra_tokens = {i: t for i, t in enumerate(tokens[1:], start=1)}
    results = await asyncio.gather(
        *[start_client(cid, tok) for cid, tok in extra_tokens.items()]
    )

    for result in results:
        if result is None:
            continue
        client_id, client = result
        tg_clients[client_id] = client
        active_loads[client_id] = 0

    if len(tg_clients) > 1:
        logger.info(f"Multi-client mode enabled with {len(tg_clients)} bot(s)")
    else:
        logger.warning("Multi-client mode requested but no extra bots started successfully")


def pick_client() -> int:
    return min(active_loads, key=active_loads.get)
