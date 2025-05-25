import logging
import os
import threading
import time
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.background import BackgroundScheduler
import yfinance as yf

# --- Config
API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
app = Flask(__name__)
scheduler = BackgroundScheduler()

# --- Market check logic
def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)

        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)

            if last_close_value > 1.09:  # Dummy ICT condition
                strategies_used = ["Liquidity Grab", "Breaker Block"]
                tp1 = last_close_value + 0.0015
                tp2 = last_close_value + 0.0030
                tp3 = last_close_value + 0.0050
                sl = last_close_value - 0.0020

                msg = (
                    "<b>📡 ICT Strategy Signal</b>\n"
                    "Pair: <b>EURUSD</b>\n"
                    f"📊 Entry: <code>{last_close_value:.5f}</code>\n"
                    f"🎯 TP1: <code>{tp1:.5f}</code>\n"
                    f"🎯 TP2: <code>{tp2:.5f}</code>\n"
                    f"🎯 TP3: <code>{tp3:.5f}</code>\n"
                    f"🛑 SL: <code>{sl:.5f}</code>\n"
                    f"🧠 Strategies: <i>{', '.join(strategies_used)}</i>"
                )
                bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# --- Start loop in thread
def start_strategy_loop():
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()

# --- Telegram command
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

@app.route("/")
def home():
    return "Bot is alive."

# --- Polling + loop thread
def start_bot():
    logging.basicConfig(level=logging.INFO)
    dp.message.register(status_handler, Command(commands=["status"]))
    start_strategy_loop()
    dp.run_polling(bot)

if __name__ == "__main__":
    thread = threading.Thread(target=start_bot)
    thread.start()
    app.run(host="0.0.0.0", port=8080)










