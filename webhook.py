import os
import logging
import asyncio
from flask import Flask, request, Response
from aiogram import Bot, Dispatcher, types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------- Environment Variables --------
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # Например: https://your-app.onrender.com
ADMIN_ID = os.environ.get('ADMIN_ID')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # опционально

SHOP_URL = f"https://{GITHUB_USERNAME}.github.io/chapman_shop/"

# -------- Flask App --------
app = Flask(__name__)

# -------- Bot & Dispatcher --------
bot = Bot(token=BOT_TOKEN)
Bot.set_current(bot)  # важно для работы message.answer вне executor
dp = Dispatcher(bot)

# -------- Flask Routes --------
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    logger.info("Webhook POST received")

    if WEBHOOK_SECRET:
        secret = request.headers.get("x-webhook-secret", "")
        if secret != WEBHOOK_SECRET:
            logger.warning("Invalid webhook secret")
            return Response(status=403)

    try:
        update = types.Update.to_object(request.get_json(force=True))
        # Используем asyncio.run вместо создания нового цикла
        asyncio.run(dp.process_update(update))
        return Response(status=200)
    except Exception as e:
        logger.exception("Failed to process update")
        return Response(status=500)

# -------- Handlers --------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "Открыть магазин",
        web_app=types.WebAppInfo(url=SHOP_URL)
    ))
    await message.answer(
        "Добро пожаловать в Chapman Shop! Нажмите кнопку чтобы открыть магазин:",
        reply_markup=kb
    )

@dp.message_handler()
async def echo_all(message: types.Message):
    logger.info("Message from %s: %s", message.from_user.id, message.text or "(no text)")

# -------- Set webhook on startup --------
def set_webhook():
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not configured")
        return
    webhook_url = WEBHOOK_URL.rstrip("/") + "/webhook"
    asyncio.run(bot.set_webhook(webhook_url))
    logger.info("Webhook set to: %s", webhook_url)

# -------- Main --------
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
