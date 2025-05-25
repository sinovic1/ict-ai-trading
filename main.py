import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import yfinance as yf

# Load environment variables
API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# ✅ Async strategy check
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, lambda: yf.download("EURUSD=X", period="1d", interval="1m"))

        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)

            if last_close_value > 1.09:  # dummy ICT strategy
                msg = (
                    "📈 <b>ICT Strategy Signal</b>\n"
                    "Pair: EURUSD\n"
                    f"Entry: {last_close_value:.5f}\n"
                    "TP1: +15 pips\nTP2: +30 pips\nTP3: +50 pips\n"
                    "SL: -20 pips"
                )
                await bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# ✅ Loop scheduler (called directly now in async context)
async def loop_checker():
    await check_strategies()

# Register command
async def status_handler(message: types.Message):
    if str(message.from_user.id) == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# Web ping route
@app.route("/")
def home():
    return "Bot is alive."

# Main async startup
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)

    dp.message.register(status_handler, Command(commands=["status"]))
    scheduler.add_job(loop_checker, "interval", minutes=1)
    scheduler.start()

    await dp.start_polling(bot)

# Launch
if __name__ == "__main__":
    asyncio.run(main())








