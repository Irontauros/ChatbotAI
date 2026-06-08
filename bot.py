from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ActivityHandler,
    TurnContext
)
import requests
from dotenv import load_dotenv
import os

load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_PASSWORD = os.getenv("APP_PASSWORD")
API_URL = os.getenv("API_URL")


# ---------------- BOT LOGIC ----------------
class MyBot(ActivityHandler):

    async def on_message_activity(self, turn_context: TurnContext):
        user_message = turn_context.activity.text

        try:
            res = requests.post(
                API_URL,
                json={"description": user_message},
                timeout=10
            )

            data = res.json()

            reply = (
                f"🧠 Category: {data.get('category')}\n"
                f"⚡ Priority: {data.get('priority')}\n"
                f"💡 Solution: {data.get('solution')}\n"
                f"📊 Confidence: {data.get('confidence_label')}"
            )

        except Exception as e:
            reply = f"❌ Erro: {str(e)}"

        await turn_context.send_activity(reply)


bot = MyBot()


# ---------------- ADAPTER ----------------
settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(settings)


async def messages(req):
    body = await req.json()
    auth_header = req.headers.get("Authorization", "")

    response = await adapter.process_activity(
        body,
        auth_header,
        bot.on_turn
    )

    return web.Response(status=200)


# ---------------- SERVER ----------------
app = web.Application()
app.router.add_post("/api/messages", messages)


if __name__ == "__main__":
    print("Bot running on http://localhost:3978")
    web.run_app(app, port=3978)