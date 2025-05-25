import asyncio
import logging
import os
from threading import Thread
from datetime import datetime
import numpy as np
import pandas as pd

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
from dotenv import load_dotenv
import yfinance as yf

# Load .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

last_signal_time = None  # to avoid duplicates

@app.route("/")
def home():
    return "Bot is alive."

def detect_liquidity_sweep(data):
    recent_lows = data['Low'].rolling(window=10).min()
    sweep = data['Low'] < recent_lows.shift(1)
    return sweep

def detect_mss(data):
    return (data['High'] > data['High'].shift(1)) & (data['Low'] < data['Low'].shift(1))

def detect_fvg(data):
    fvg = (data['Low'].shift(-1) > data['High']) & (data['Low'].shift(-1) - data['High'] > 0.0001)
    return fvg

def detect_ote(data):
    high = data['High'].rolling(window=20).max()
    low = data['Low'].rolling(window=20).min()
    retrace_zone = low + (high - low) * 0.618
    return data['Close'] > retrace_zone

async def check_strategies():
    global last_signal_time
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False).tail(50)
        if data.empty or len(data) < 20:
            return

        data.dropna(inplace=True)

        # Apply ICT strategies
        sweep = detect_liquidity_sweep(data)
        mss = detect_mss(data)
        fvg = detect_fvg(data)
        ote = detect_ote(data)

        combined = sweep & mss & fvg & ote

        if combined.any():
            if last_signal_time and (datetime.now() - last_signal_time).seconds < 300:
                return  # prevent duplicate signals

            last_price = float(data["Close"].iloc[-1])
            tp1 = round(last_price + 0.0015, 5)
            tp2 = round(last_price + 0.003, 5)
            tp3 = round(last_price + 0.005, 5)
            sl = round(last_price - 0.002, 5)

            message = (
                "<b>📈 ICT Buy Signal</b>\n"
                f"Pair: EURUSD\n"
                f"Entry: {last_price:.5f}\n"
                f"TP1: {tp1}\n"
                f"TP2: {tp2}\n"
                f"TP3: {tp3}\n"
                f"SL: {sl}\n"
                f"🧠 Strategy: MSS + FVG + OTE + Liquidity Sweep"
            )

            await bot.send_message(chat_id=OWNER_ID, text=message)
            last_signal_time = datetime.now()

    except Exception as e:
        logging.error(f"❌ Error: {e}")

@dp.message(Command("status"))
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

async def start_bot():
    dp.include_router(dp)
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Thread(target=lambda: asyncio.run(start_bot())).start()
    app.run(host="0.0.0.0", port=8080)



















