# filename: bot_webhook.py
# Flask + aiogram bot using webhook mode
# Requirements: Flask, aiogram (v2.x), gunicorn
# Environment variables: BOT_TOKEN, WEBHOOK_URL (public URL, e.g. https://your-service.onrender.com), ADMIN_ID, GITHUB_USERNAME, WEBHOOK_SECRET (optional)

import os
import logging
import asyncio
from flask import Flask, request, Response
from aiogram import Bot, Dispatcher, types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN') or "<BOT_TOKEN>"
WEBHOOK_URL = os.environ.get('WEBHOOK_URL') or "<BOT_WEBHOOK_URL>"  # e.g. https://your-app.onrender.com
ADMIN_ID = os.environ.get('ADMIN_ID') or "<ADMIN_ID>"
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME') or "<GITHUB_USERNAME>"
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # optional secret expected in incoming requests from frontend

app = Flask(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

SHOP_URL = f"https://{GITHUB_USERNAME}.github.io/chapman-shop/"

@app.route('/', methods=['GET'])
def health():
    return 'OK', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Optional: check shared secret header if provided by sender
        if WEBHOOK_SECRET:
            incoming = request.headers.get('x-webhook-secret', '')
            if not incoming or incoming != WEBHOOK_SECRET:
                logger.warning("Invalid webhook secret on /webhook")
                return Response(status=403)

        update_json = request.get_json(force=True)
        update = types.Update.to_object(update_json)

        # Process update with aiogram
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(dp.process_update(update))
        loop.close()
        return Response(status=200)
    except Exception as e:
        logger.exception("Failed to process update: %s", e)
        return Response(status=500)

# Handlers
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    try:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Открыть магазин", web_app=types.WebAppInfo(url=SHOP_URL)))
        await message.answer("Добро пожаловать в Chapman Shop! Нажмите кнопку чтобы открыть магазин:", reply_markup=kb)
    except Exception as e:
        logger.exception("Error in /start handler: %s", e)

@dp.message_handler()
async def echo_all(message: types.Message):
    # Handle web_app_data if present (when user submits via Telegram WebApp)
    try:
        if hasattr(message, 'web_app_data') and message.web_app_data:
            try:
                data_text = message.web_app_data.data
                payload = None
                try:
                    import json
                    payload = json.loads(data_text)
                except Exception:
                    payload = {"raw": data_text}
                # Format a readable message for admin
                text_lines = []
                text_lines.append("<b>Order from WebApp (bot)</b>")
                text_lines.append(f"⏱ {message.date.isoformat()}")
                text_lines.append("")
                text_lines.append(f"<pre>{json.dumps(payload, ensure_ascii=False, indent=2)}</pre>")
                # send to admin
                await bot.send_message(chat_id=ADMIN_ID, text="\n".join(text_lines), parse_mode='HTML')
                return
            except Exception as e:
                logger.exception("Failed to process web_app_data: %s", e)

        # simple echo/log for other messages
        logger.info("Received message from %s: %s", message.from_user.id, message.text or "(no text)")
    except Exception as e:
        logger.exception("Error in echo_all handler: %s", e)

def set_webhook():
    if not WEBHOOK_URL or WEBHOOK_URL.startswith("<"):
        logger.warning("WEBHOOK_URL not configured. Skipping automatic webhook set.")
        return
    webhook_url = WEBHOOK_URL.rstrip('/') + '/webhook'
    logger.info("Setting webhook to: %s", webhook_url)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot.set_webhook(webhook_url))
    except Exception as e:
        logger.exception("Failed to set webhook: %s", e)

if __name__ == '__main__':
    # Optionally set webhook automatically on startup
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
