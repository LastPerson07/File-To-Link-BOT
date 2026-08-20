import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

from pyrogram import Client
from config import config


class AppClient(Client):
    def __init__(self):
        super().__init__(
            name=config.session,
            api_id=config.api_id,
            api_hash=config.api_hash,
            bot_token=config.bot_token,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=config.sleep_threshold,
        )


app_bot = AppClient()

tg_clients = {}
active_loads = {}
