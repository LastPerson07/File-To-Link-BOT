from aiohttp import web

from .routes import routes


async def create_app():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
