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
OWNER_ID = int(os.getenv("OWNER_ID"))  # Telegram user ID

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# ✅ ICT Strategy Check (Safe + Correct)
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m")
        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)  # ✅ Convert safely

            if last_close_value > 1.09:  # ✅ Dummy condition
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

# 🔁 Job wrapper
def loop_checker():
    asyncio.run(check_strategies())

# ⏱️ Schedule loop
scheduler.add_job(loop_checker, "interval", minutes=1)

# 🔘 Bot command: /status
async def status_handler(message: types.Message):
    if str(message.from_user.id) == str(OWNER_ID):
        await message.answer("✅ Bot is running and healthy.")

# 🌐 Keep-alive route
@app.route("/")
def home():
    return "Bot is alive."

# 🚀 Start everything
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.message.register(status_handler, Command(commands=["status"]))
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())






