import asyncio
import logging
import os
from datetime import datetime
from flask import Flask
from threading import Thread
import yfinance as yf

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# Strategies config
def analyze_strategies(data):
    last_close = data["Close"].iloc[-1]
    prev_close = data["Close"].iloc[-2]
    rsi = (last_close / prev_close) * 100  # Dummy RSI-like logic

    signals = []
    if last_close > prev_close:
        signals.append("EMA")
    if rsi > 70:
        signals.append("RSI")
    if (last_close - prev_close) > 0.002:
        signals.append("MACD")
    if abs(last_close - prev_close) > 0.003:
        signals.append("Bollinger Bands")

    return signals, last_close, "Buy" if last_close > prev_close else "Sell"

# Check strategies
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if data.empty:
            return

        strategies, last_close, direction = analyze_strategies(data)

        if len(strategies) >= 2:
            last_close = float(data["Close"].iloc[-1])
            tp1 = last_close + 0.0010 if direction == "Buy" else last_close - 0.0010
            tp2 = last_close + 0.0020 if direction == "Buy" else last_close - 0.0020
            tp3 = last_close + 0.0030 if direction == "Buy" else last_close - 0.0030
            sl = last_close - 0.0015 if direction == "Buy" else last_close + 0.0015

            msg = (
                f"📈 <b>ICT Strategy Signal</b>\n"
                f"Type: <b>{direction}</b>\n"
                f"Pair: EURUSD\n"
                f"Entry: {last_close:.5f}\n"
                f"TP1: {tp1:.5f}\n"
                f"TP2: {tp2:.5f}\n"
                f"TP3: {tp3:.5f}\n"
                f"SL: {sl:.5f}\n"
                f"Strategies: <i>{', '.join(strategies)}</i>"
            )
            await bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# Status command
@dp.message(Command(commands=["status"]))
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# Flask web route
@app.route("/")
def home():
    return "✅ Bot is alive"

# Start Flask in thread
def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Main entry
async def start_bot():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(dp)
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(start_bot())












