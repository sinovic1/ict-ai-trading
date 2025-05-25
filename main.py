import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import yfinance as yf

# ---🔐 Your bot token and owner ID ---
API_TOKEN = os.getenv("BOT_TOKEN") or "7134641176:AAHtLDFCIvlnXVQgX0CHWhbgFUfRyuhbmXU"
OWNER_ID = int(os.getenv("OWNER_ID") or 7469299312)

# ---🤖 Aiogram setup ---
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
app = Flask(__name__)

# ---📈 ICT Strategy Checker ---
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)

        if data.empty:
            logging.warning("⚠️ No market data returned.")
            return

        close_series = data["Close"].dropna()

        if close_series.empty:
            logging.warning("⚠️ Close prices missing or empty.")
            return

        last_close = close_series.iloc[-1]

        if float(last_close) > 1.09:  # Example dummy condition
            msg = (
                "📈 <b>ICT Strategy Signal</b>\n"
                "Pair: EURUSD\n"
                f"Entry: {last_close:.5f}\n"
                "TP1: +15 pips\nTP2: +30 pips\nTP3: +50 pips\n"
                "SL: -20 pips"
            )
            await bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# ---📅 Run strategies periodically ---
async def loop_checker():
    await check_strategies()

# ---💬 Telegram command handler ---
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# ---🌐 Web route for Koyeb health check ---
@app.route("/")
def home():
    return "✅ ICT Bot is alive."

# ---🚀 Main async startup ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.message.register(status_handler, Command(commands=["status"]))
    scheduler.add_job(loop_checker, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

# ---🔁 Entry point ---
if __name__ == "__main__":
    asyncio.run(main())


