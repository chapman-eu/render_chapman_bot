import os
import logging
import asyncio
from flask import Flask, request, Response
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
ADMIN_ID = os.environ.get('ADMIN_ID')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # optional

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN, session=AiohttpSession())
dp = Dispatcher()

SHOP_URL = f"https://{GITHUB_USERNAME}.github.io/chapman-shop/"

# ---------------- Routes ----------------
@app.route('/', methods=['GET'])
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    logger.info("Webhook POST received")
    if WEBHOOK_SECRET:
        incoming = request.headers.get('x-webhook-secret', '')
        if incoming != WEBHOOK_SECRET:
            logger.warning("Invalid webhook secret")
            return Response(status=403)
    try:
        update_json = request.get_json(force=True)
        await dp.feed_update(bot, update_json)
        return Response(status=200)
    except Exception as e:
        logger.exception("Failed to process update")
        return Response(status=500)

# ---------------- Handlers ----------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=SHOP_URL))]
    ])
    await message.answer("Добро пожаловать в Chapman Shop! Нажмите кнопку чтобы открыть магазин:", reply_markup=kb)

@dp.message()
async def echo_all(message: Message):
    logger.info("Message from %s: %s", message.from_user.id, message.text or "(no text)")

# ---------------- Webhook Setup ----------------
async def set_webhook():
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not configured")
        return
    webhook_url = WEBHOOK_URL.rstrip("/") + "/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

# ---------------- Main ----------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
