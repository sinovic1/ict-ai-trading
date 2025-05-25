import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from threading import Thread
from flask import Flask
import yfinance as yf

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# ✅ Use the old way to set parse_mode
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

last_signal_time = None
last_signal_type = None

def detect_buy_signal(data):
    return data["Close"].iloc[-1] > data["Open"].iloc[-1]

def detect_sell_signal(data):
    return data["Close"].iloc[-1] < data["Open"].iloc[-1]

async def check_strategies():
    global last_signal_time, last_signal_type
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m")
        if data.empty:
            return

        now = datetime.utcnow()
        last_close = data["Close"].iloc[-1]
        entry = float(last_close)

        TP1 = round(entry + 0.0015, 5)
        TP2 = round(entry + 0.0030, 5)
        TP3 = round(entry + 0.0050, 5)
        SL = round(entry - 0.0020, 5)

        signal_type = None
        if detect_buy_signal(data):
            signal_type = "Buy"
        elif detect_sell_signal(data):
            signal_type = "Sell"

        if signal_type and (last_signal_type != signal_type or not last_signal_time or (now - last_signal_time).seconds > 300):
            last_signal_type = signal_type
            last_signal_time = now

            msg = (
                f"<b>{signal_type} Signal Detected</b>\n"
                f"Pair: EURUSD\n"
                f"Entry: {entry:.5f}\n"
                f"TP1: {TP1}\nTP2: {TP2}\nTP3: {TP3}\n"
                f"SL: {SL}\n"
                f"Strategies Used: ICT Logic"
            )
            await bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

@dp.message(Command(commands=["status"]))
async def status_command(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

@app.route("/")
def home():
    return "Bot is alive."

async def start_bot():
    dp.include_router(dp)
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    Thread(target=lambda: asyncio.run(start_bot())).start()
    app.run(host="0.0.0.0", port=8080)

















