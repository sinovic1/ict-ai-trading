import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask
from threading import Thread
import random

# === CONFIG ===
BOT_TOKEN = "7923000946:AAEx8TZsaIl6GL7XUwPGEM6a6-mBNfKwUz8"
ALLOWED_USER_ID = 7469299312
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "EURJPY", "GBPJPY", "XAUUSD", "NAS100"]

# === SETUP ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
last_check_time = time.time()

# === ICT STRATEGY SIMULATION (Mock Logic) ===
def check_ict_strategy(pair):
    # Simulating strong confluence (60% chance of no signal)
    if random.random() < 0.4:
        price = round(random.uniform(1.1, 1.5), 5)
        sl = round(price - 0.0020, 5)
        tp1 = round(price + 0.0020, 5)
        tp2 = round(price + 0.0040, 5)
        tp3 = round(price + 0.0060, 5)
        order_type = random.choice(["Buy Limit", "Sell Stop", "Buy Stop", "Sell Limit"])
        return {
            "pair": pair,
            "entry": price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "order_type": order_type
        }
    return None

# === MESSAGE SENDER ===
async def send_signal(signal):
    msg = f"""📈 <b>Signal: {signal['pair']}</b>
<b>Type:</b> {signal['order_type']}
<b>Entry:</b> {signal['entry']}
<b>Stop Loss:</b> {signal['sl']}
<b>Take Profit 1:</b> {signal['tp1']}
<b>Take Profit 2:</b> {signal['tp2']}
<b>Take Profit 3:</b> {signal['tp3']}"""
    await bot.send_message(chat_id=ALLOWED_USER_ID, text=msg)

# === CHECK STRATEGIES PERIODICALLY ===
async def strategy_loop():
    global last_check_time
    while True:
        for pair in PAIRS:
            signal = check_ict_strategy(pair)
            if signal:
                await send_signal(signal)
        last_check_time = time.time()
        await asyncio.sleep(900)  # every 15 mins

# === TELEGRAM COMMANDS ===
@dp.message()
async def handle_msg(msg: types.Message):
    if msg.chat.id != ALLOWED_USER_ID:
        return
    if msg.text.lower() == "/status":
        now = time.time()
        delay = now - last_check_time
        if delay < 1800:
            await msg.answer("✅ Bot is running and checking signals.")
        else:
            await msg.answer("⚠️ Warning: Strategy loop may have stopped!")

# === FLASK FOR KEEP-ALIVE ===
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot running!'

# === START BOT ===
async def start_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Start strategy loop in background
    Thread(target=lambda: asyncio.run(strategy_loop())).start()
    # Start bot
    Thread(target=lambda: asyncio.run(start_bot())).start()
    # Start Flask
    app.run(host="0.0.0.0", port=8080)




















