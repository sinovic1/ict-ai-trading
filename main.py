import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf

# ✅ Load from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# ✅ Aiogram Bot
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# ✅ Signal strategy check
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m")
        if data.empty:
            return

        last_close = data["Close"].iloc[-1]
        last_close_value = float(last_close)

        # Dummy ICT logic: Detect buy signal above 1.13
        if last_close_value > 1.13:
            tp1 = last_close_value + 0.0015
            tp2 = last_close_value + 0.0030
            tp3 = last_close_value + 0.0050
            sl = last_close_value - 0.0020
            msg = (
                f"<b>📈 Buy Signal Detected</b>\n"
                f"Pair: EURUSD\n"
                f"Entry: {last_close_value:.5f}\n"
                f"TP1: {tp1:.5f}\n"
                f"TP2: {tp2:.5f}\n"
                f"TP3: {tp3:.5f}\n"
                f"SL: {sl:.5f}\n"
                f"Strategies Used: ICT Strategy (dummy logic)"
            )
            await bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# ✅ Status command handler
@dp.message(Command("status"))
async def status(message: Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and responding.")

# ✅ Flask route
@app.route("/")
def home():
    return "✅ Bot is alive."

# ✅ Bot start logic
async def start_bot():
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ✅ Main
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 8080}).start()
    asyncio.run(start_bot())


















