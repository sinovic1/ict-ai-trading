import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import yfinance as yf
import os

API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# 📌 Store last signal to avoid duplicates
last_signal = {"pair": None, "entry": None, "direction": None}

# 📈 Example ICT strategy logic
async def check_strategies():
    try:
        logging.info("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)  # safe casting

            # Dummy strategy example:
            is_buy = last_close_value > 1.09
            is_sell = last_close_value < 1.07
            strategies_used = []

            if is_buy:
                direction = "Buy"
                strategies_used.append("Breakout (Dummy)")
            elif is_sell:
                direction = "Sell"
                strategies_used.append("Rejection (Dummy)")
            else:
                return  # no signal

            # Avoid duplicate alerts
            if (
                last_signal["entry"] == last_close_value and
                last_signal["direction"] == direction
            ):
                return

            # ✅ Update last signal
            last_signal.update({
                "pair": "EURUSD",
                "entry": last_close_value,
                "direction": direction
            })

            entry = last_close_value
            tp1 = round(entry + 0.0015, 5) if is_buy else round(entry - 0.0015, 5)
            tp2 = round(entry + 0.0030, 5) if is_buy else round(entry - 0.0030, 5)
            tp3 = round(entry + 0.0050, 5) if is_buy else round(entry - 0.0050, 5)
            sl = round(entry - 0.0020, 5) if is_buy else round(entry + 0.0020, 5)

            msg = (
                f"📡 <b>ICT Signal Detected</b>\n"
                f"<b>Direction:</b> {direction}\n"
                f"<b>Pair:</b> EURUSD\n"
                f"<b>Entry:</b> {entry:.5f}\n"
                f"<b>TP1:</b> {tp1:.5f}\n"
                f"<b>TP2:</b> {tp2:.5f}\n"
                f"<b>TP3:</b> {tp3:.5f}\n"
                f"<b>SL:</b> {sl:.5f}\n"
                f"<b>Strategies:</b> {', '.join(strategies_used)}"
            )
            await bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# ✅ /status command
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# ✅ Start polling in background
async def start_bot():
    logging.basicConfig(level=logging.INFO)
    dp.message.register(status_handler, Command(commands=["status"]))
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ✅ Flask endpoint for Railway/Koyeb uptime check
@app.route("/")
def home():
    return "✅ ICT Bot is alive."

# ✅ Main entry point
def main():
    from threading import Thread
    Thread(target=lambda: asyncio.run(start_bot())).start()
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()












