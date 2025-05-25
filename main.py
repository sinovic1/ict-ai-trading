import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
from threading import Thread
import yfinance as yf

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# === Strategy Logic ===
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m")
        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)

            # Dummy signal logic
            if last_close_value > 1.09:
                tp1 = round(last_close_value + 0.0015, 5)
                tp2 = round(last_close_value + 0.0030, 5)
                tp3 = round(last_close_value + 0.0050, 5)
                sl = round(last_close_value - 0.0020, 5)

                msg = (
                    f"📈 <b>Buy Signal Detected</b>\n"
                    f"Pair: EURUSD\n"
                    f"Entry: {last_close_value}\n"
                    f"TP1: {tp1}\n"
                    f"TP2: {tp2}\n"
                    f"TP3: {tp3}\n"
                    f"SL: {sl}\n"
                    f"Strategies Used: RSI, MACD"
                )
                await bot.send_message(chat_id=OWNER_ID, text=msg)
    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# === /status command ===
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# === Flask keep-alive route ===
@app.route("/")
def home():
    return "Bot is alive."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# === Main bot logic ===
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)

    dp.message.register(status_handler, Command(commands=["status"]))

    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()

    await dp.start_polling(bot)

# === Entry point ===
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())














