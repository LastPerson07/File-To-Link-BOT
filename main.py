import sys
import asyncio
import logging
from datetime import date, datetime
import pytz
from aiohttp import web
from pyrogram import idle, __version__ as pyrogram_version
from pyrogram.raw.all import layer
import pyrogram.utils
from config import ON_HEROKU, LOG_CHANNEL, ADMINS, PORT
from helpers import app_state, keep_alive
from texts import Texts
from api.helpers import __version__ as app_version
from api import create_app
from api.client import app_bot
from api.client.launcher import initialize_clients
from api.server.logger_setup import setup_support_logger
from database.store import store

logger = setup_support_logger()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(
        "UNHANDLED EXCEPTION",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

sys.excepthook = handle_exception

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

async def boot_app():
    logging.info("Credit - Telegram @LastPerson07")

    try:
        await initialize_clients()

        logging.info("Starting app_bot...")
        await app_bot.start()

        try:
            await store.ensure_indexes()
        except Exception:
            logger.error("ENSURE INDEXES FAILED", exc_info=True)

        if ON_HEROKU:
            asyncio.create_task(keep_alive())

        me = await app_bot.get_me()
        app_state.U_NAME = me.username
        app_state.B_NAME = me.first_name

        logging.info(
            f"{me.first_name} with Pyrogram v{pyrogram_version} (Layer {layer}) started on {me.username}."
        )

        tz = pytz.timezone("Asia/Kolkata")
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")

        try:
            await app_bot.send_message(
                chat_id=LOG_CHANNEL,
                text=Texts.RESTART_TXT.format(today, time, app_version)
            )
        except Exception:
            logger.error("LOG CHANNEL ERROR", exc_info=True)

        if ADMINS:
            try:
                await app_bot.send_message(
                    chat_id=ADMINS[0],
                    text="<b>ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ !!</b>"
                )
            except Exception:
                pass

        app = web.AppRunner(await create_app())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logging.info(f"Web Server Started on Port {PORT}")

        await idle()

    except Exception:
        logger.critical("STARTUP SEQUENCE FAILED", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(boot_app())
    except KeyboardInterrupt:
        logging.info("Service Stopped Bye 👋")
    except Exception:
        logger.critical("CRITICAL RUNTIME ERROR", exc_info=True)