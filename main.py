import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
from threading import Thread
import os
import yfinance as yf

# === Load Secrets ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# === Setup Bot & Dispatcher ===
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# === Track Last Alert ===
last_signal = None

# === ICT STRATEGIES (DUMMY CHECKS) ===
def ict_fvg(data):  # Fake example logic
    return data["Close"].iloc[-1] > data["Open"].iloc[-1]

def ict_choch(data):
    return data["High"].iloc[-1] > data["High"].iloc[-2]

def ict_bos(data):
    return data["Low"].iloc[-1] < data["Low"].iloc[-2]

def get_ict_signals(data):
    signals = []
    if ict_fvg(data): signals.append("FVG")
    if ict_choch(data): signals.append("CHoCH")
    if ict_bos(data): signals.append("BOS")
    return signals

# === Signal Generator ===
async def check_strategies():
    global last_signal
    try:
        logging.info("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if data.empty: return

        current_price = float(data["Close"].iloc[-1])
        signals = get_ict_signals(data)

        if len(signals) >= 2:
            signal_id = f"{current_price:.5f}-{','.join(signals)}"
            if signal_id == last_signal:
                return  # ⛔ Prevent repeat

            last_signal = signal_id
            direction = "Buy" if data["Close"].iloc[-1] > data["Open"].iloc[-1] else "Sell"

            tp1 = round(current_price + 0.0015, 5) if direction == "Buy" else round(current_price - 0.0015, 5)
            tp2 = round(current_price + 0.0030, 5) if direction == "Buy" else round(current_price - 0.0030, 5)
            tp3 = round(current_price + 0.0050, 5) if direction == "Buy" else round(current_price - 0.0050, 5)
            sl = round(current_price - 0.0020, 5) if direction == "Buy" else round(current_price + 0.0020, 5)

            msg = (
                f"📊 <b>{direction} Signal Detected</b>\n"
                f"<b>Pair:</b> EURUSD\n"
                f"<b>Entry:</b> {current_price:.5f}\n"
                f"<b>TP1:</b> {tp1}\n"
                f"<b>TP2:</b> {tp2}\n"
                f"<b>TP3:</b> {tp3}\n"
                f"<b>SL:</b> {sl}\n"
                f"<b>Strategies Used:</b> {', '.join(signals)}"
            )
            await bot.send_message(chat_id=OWNER_ID, text=msg)
    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# === Schedule job ===
scheduler.add_job(check_strategies, "interval", minutes=1)

# === Telegram Commands ===
@dp.message(Command("status"))
async def status(message: Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is working fine.")

# === Flask keep-alive ===
@app.route("/")
def home():
    return "Bot is live."

# === Start Polling ===
async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler.start()
    Thread(target=lambda: asyncio.run(start_bot())).start()
    app.run(host="0.0.0.0", port=8080)
















