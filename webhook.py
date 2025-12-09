# --- snippet ---
import os
import logging
import asyncio
from flask import Flask, request, Response
from aiogram import Bot, Dispatcher, types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
ADMIN_ID = os.environ.get('ADMIN_ID')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # optional

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

SHOP_URL = f"https://{GITHUB_USERNAME}.github.io/chapman-shop/"

# global event loop
loop = asyncio.get_event_loop()

@app.route('/', methods=['GET'])
def health():
    return 'OK', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("Webhook POST received")
    if WEBHOOK_SECRET:
        incoming = request.headers.get('x-webhook-secret', '')
        if incoming != WEBHOOK_SECRET:
            logger.warning("Invalid webhook secret")
            return Response(status=403)
    try:
        update = types.Update.to_object(request.get_json(force=True))
        loop.run_until_complete(dp.process_update(update))
        return Response(status=200)
    except Exception as e:
        logger.exception("Failed to process update")
        return Response(status=500)

# Handlers
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Открыть магазин", web_app=types.WebAppInfo(url=SHOP_URL)))
    await message.answer("Добро пожаловать в Chapman Shop! Нажмите кнопку чтобы открыть магазин:", reply_markup=kb)

@dp.message_handler()
async def echo_all(message: types.Message):
    logger.info("Message from %s: %s", message.from_user.id, message.text or "(no text)")

def set_webhook():
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not configured")
        return
    webhook_url = WEBHOOK_URL.rstrip('/') + '/webhook'
    logger.info("Setting webhook to: %s", webhook_url)
    loop.run_until_complete(bot.set_webhook(webhook_url))

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
