import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import yfinance as yf

# --- Config
API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# --- Market check logic
def check_strategies_sync():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)

            # Dummy ICT signal logic
            if last_close_value > 1.09:
                # Simulated strategy confirmation
                strategies_triggered = ["Liquidity Grab", "Breaker Block"]

                # Calculate TP/SL levels (example)
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
                    f"🧠 Strategies: <i>{', '.join(strategies_triggered)}</i>"
                )

                asyncio.run(bot.send_message(chat_id=OWNER_ID, text=msg))

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# --- Scheduler Job
async def loop_checker():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, check_strategies_sync)

# --- Status Command
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# --- Flask Route
@app.route("/")
def home():
    return "Bot is alive."

# --- Main Entry
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.message.register(status_handler, Command(commands=["status"]))
    scheduler.add_job(loop_checker, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())









