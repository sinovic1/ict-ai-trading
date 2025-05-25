import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import yfinance as yf
from flask import Flask
import threading

API_TOKEN = "7134641176:AAHtLDFCIvlnXVQgX0CHWhbgFUfRyuhbmXU"
ALLOWED_USER_ID = 7469299312  # your Telegram ID
FOREX_PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X"]

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# --- ICT STRATEGY PLACEHOLDER ---
def ict_strategy(data):
    # Example ICT condition (simplified)
    if data['Close'].iloc[-1] > data['Open'].iloc[-1]:  # Bullish candle
        entry = round(data['Close'].iloc[-1], 5)
        sl = round(entry - 0.0020, 5)
        tp1 = round(entry + 0.0020, 5)
        tp2 = round(entry + 0.0040, 5)
        tp3 = round(entry + 0.0060, 5)
        return True, entry, sl, tp1, tp2, tp3
    return False, None, None, None, None, None

async def check_ict_strategies():
    for pair in FOREX_PAIRS:
        data = yf.download(pair, period="1d", interval="15m")
        if data.empty:
            continue
        signal, entry, sl, tp1, tp2, tp3 = ict_strategy(data)
        if signal:
            msg = (
                f"📉 <b>ICT Signal for {pair.replace('=X','')}</b>\n"
                f"Entry: <b>{entry}</b>\n"
                f"SL: <b>{sl}</b>\n"
                f"TP1: <b>{tp1}</b>\n"
                f"TP2: <b>{tp2}</b>\n"
                f"TP3: <b>{tp3}</b>"
            )
            await bot.send_message(ALLOWED_USER_ID, msg)

@dp.message()
async def handle_message(message: types.Message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    if message.text.lower() == "/status":
        await message.reply("✅ ICT Bot is running and healthy.")

def loop_checker():
    logging.info(f"🔄 ICT Bot checking market at {datetime.utcnow().isoformat()}")
    asyncio.run(check_ict_strategies())

@app.route('/')
def home():
    return "ICT Trading Bot is running."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def main():
    scheduler.add_job(loop_checker, "interval", minutes=1)
    scheduler.start()
    threading.Thread(target=run_flask).start()
    dp.run_polling(bot)

if __name__ == "__main__":
    logging.info("✅ Webhook cleared")
    main()
