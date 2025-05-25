import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import yfinance as yf
from threading import Thread
from dotenv import load_dotenv

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Initialize
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# Store last signal
last_signal = {"side": None, "entry": None}

# === STRATEGY FUNCTIONS ===
def rsi_strategy(data):
    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]
    return "RSI" if last_rsi < 30 or last_rsi > 70 else None

def macd_strategy(data):
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] < signal.iloc[-2]:
        return "MACD"
    if macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] > signal.iloc[-2]:
        return "MACD"
    return None

def direction(data):
    return "Buy" if data["Close"].iloc[-1] > data["Open"].iloc[-1] else "Sell"

# === CHECK STRATEGIES ===
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="2d", interval="1m", auto_adjust=True)
        if data.empty:
            return

        last_close = data["Close"].iloc[-1]
        entry = float(last_close)
        side = direction(data)

        strategies_used = list(filter(None, [rsi_strategy(data), macd_strategy(data)]))

        if len(strategies_used) >= 2:
            if last_signal["entry"] == entry and last_signal["side"] == side:
                return  # skip if same signal

            tp1 = entry + 0.0015 if side == "Buy" else entry - 0.0015
            tp2 = entry + 0.0030 if side == "Buy" else entry - 0.0030
            tp3 = entry + 0.0050 if side == "Buy" else entry - 0.0050
            sl  = entry - 0.0020 if side == "Buy" else entry + 0.0020

            msg = (
                f"<b>{side} Signal Detected</b>\n"
                f"Pair: EURUSD\n"
                f"Entry: {entry:.5f}\n"
                f"TP1: {tp1:.5f}\nTP2: {tp2:.5f}\nTP3: {tp3:.5f}\n"
                f"SL: {sl:.5f}\n"
                f"Strategies Used: {', '.join(strategies_used)}"
            )

            await bot.send_message(chat_id=OWNER_ID, text=msg)
            last_signal["entry"] = entry
            last_signal["side"] = side

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# === TELEGRAM HANDLER ===
@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# === FLASK KEEP ALIVE ===
@app.route("/")
def home():
    return "Bot is alive."

# === START BOT ===
async def start_bot():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.message.register(status_cmd)
    await dp.start_polling(bot)

# === MAIN ENTRY POINT ===
if __name__ == "__main__":
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()
    Thread(target=lambda: asyncio.run(start_bot())).start()
    app.run(host="0.0.0.0", port=8080)


















