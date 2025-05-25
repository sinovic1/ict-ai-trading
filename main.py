import asyncio
import logging
import os
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
import yfinance as yf

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))  # make sure it's int
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
app = Flask(__name__)
scheduler = BackgroundScheduler()

# 🧠 Remember last signal so we don’t repeat it
last_signal = {"entry": None}

# 📈 Strategy checker
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m")
        if data.empty:
            return

        last_close = data["Close"].iloc[-1]
        last_close_value = float(last_close)

        # Dummy strategy triggers
        rsi_triggered = last_close_value > 1.09
        macd_triggered = last_close_value > 1.08

        if rsi_triggered and macd_triggered:
            # Avoid repeating the same signal
            if last_signal["entry"] == last_close_value:
                print("ℹ️ Signal already sent at this price.")
                return
            last_signal["entry"] = last_close_value

            tp1 = round(last_close_value + 0.0015, 5)
            tp2 = round(last_close_value + 0.003, 5)
            tp3 = round(last_close_value + 0.005, 5)
            sl = round(last_close_value - 0.002, 5)

            msg = (
                "📈 <b>Buy Signal Detected</b>\n"
                "Pair: EURUSD\n"
                f"Entry: {last_close_value}\n"
                f"TP1: {tp1}\nTP2: {tp2}\nTP3: {tp3}\n"
                f"SL: {sl}\n"
                "Strategies Used: RSI, MACD"
            )
            await bot.send_message(chat_id=OWNER_ID, text=msg)
    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# ✅ /status command
@dp.message(Command("status"))
async def status(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# 🔁 Schedule job every minute
scheduler.add_job(lambda: asyncio.run(check_strategies()), "interval", minutes=1)

# 🧠 Bot runner
async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(dp)
    await dp.start_polling(bot)

# 🌐 Flask server to stay alive
@app.route("/")
def home():
    return "✅ Bot is alive."

# 🚀 Start everything
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler.start()
    Thread(target=lambda: asyncio.run(start_bot())).start()
    app.run(host="0.0.0.0", port=8080)















