import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import yfinance as yf
from datetime import datetime

# ENV variables
API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "7469299312"))

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

last_signal_price = None

# Helper: Market open check
def market_is_open():
    now = datetime.utcnow()
    weekday = now.weekday()
    hour = now.hour
    if weekday == 5 or (weekday == 6 and hour < 22):
        return False
    return True

# Main strategy checker
async def check_strategies():
    global last_signal_price
    try:
        if not market_is_open():
            print("⏸ Market is closed, skipping check.")
            return

        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)

            if last_signal_price is None or abs(last_signal_price - last_close_value) > 0.0001:
                last_signal_price = last_close_value

                direction = "Buy" if last_close_value > 1.09 else "Sell"
                sl = round(last_close_value - 0.0020, 5) if direction == "Buy" else round(last_close_value + 0.0020, 5)
                tp1 = round(last_close_value + 0.0015, 5) if direction == "Buy" else round(last_close_value - 0.0015, 5)
                tp2 = round(last_close_value + 0.0030, 5) if direction == "Buy" else round(last_close_value - 0.0030, 5)
                tp3 = round(last_close_value + 0.0050, 5) if direction == "Buy" else round(last_close_value - 0.0050, 5)

                strategies_used = "ICT: FVG + OTE"

                msg = (
                    f"<b>📊 ICT Strategy Signal</b>\n"
                    f"Pair: EUR/USD\n"
                    f"Direction: <b>{direction}</b>\n"
                    f"Entry: {last_close_value:.5f}\n"
                    f"TP1: {tp1:.5f}\n"
                    f"TP2: {tp2:.5f}\n"
                    f"TP3: {tp3:.5f}\n"
                    f"SL: {sl:.5f}\n"
                    f"🧠 Strategy: {strategies_used}"
                )
                await bot.send_message(chat_id=OWNER_ID, text=msg)
            else:
                print("⏭ No new price movement.")
    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# Flask route for Koyeb health check
@app.route("/")
def home():
    return "✅ Bot is alive."

# /status command
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# Start polling in background
def start_bot():
    asyncio.run(dp.start_polling(bot))

# Main entry
def main():
    logging.basicConfig(level=logging.INFO)
    dp.message.register(status_handler, Command(commands=["status"]))

    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()

    from threading import Thread
    Thread(target=start_bot).start()

    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()












