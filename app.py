from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from bot import MyBot
from dotenv import load_dotenv
import os

load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_PASSWORD = os.getenv("APP_PASSWORD")

settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(settings)

bot = MyBot()

async def messages(req):
    body = await req.json()
    auth_header = req.headers.get("Authorization", "")

    response = await adapter.process_activity(body, auth_header, bot.on_turn)
    return web.Response(status=201)

app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(app, port=3978)