import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf
from aiohttp import web

# --- Configuration
API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# --- Strategy Logic
async def check_strategies():
    try:
        print("🔄 Checking market data...")
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if not data.empty:
            last_close = data["Close"].iloc[-1]
            last_close_value = float(last_close)

            if last_close_value > 1.09:  # Dummy ICT signal condition
                tp1 = last_close_value + 0.0015
                tp2 = last_close_value + 0.0030
                tp3 = last_close_value + 0.0050
                sl = last_close_value - 0.0020
                strategies_used = ["Liquidity Grab", "Breaker Block"]

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
                await bot.send_message(chat_id=OWNER_ID, text=msg)

    except Exception as e:
        logging.error(f"❌ Error while checking EURUSD=X: {e}")

# --- Bot command
async def status_handler(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("✅ Bot is running and healthy.")

# --- Health Check Server
async def handle(request):
    return web.Response(text="Bot is alive.")

app = web.Application()
app.router.add_get("/", handle)

# --- Startup
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.message.register(status_handler, Command(commands=["status"]))
    scheduler.add_job(check_strategies, "interval", minutes=1)
    scheduler.start()

    # Start bot and web server
    await asyncio.gather(
        dp.start_polling(bot),
        web._run_app(app, port=8080)
    )

if __name__ == "__main__":
    asyncio.run(main())











