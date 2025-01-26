import os
import asyncio
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from pybit.unified_trading import HTTP
import psycopg2
from datetime import datetime, timedelta

# Telegram Bot Token
TELEGRAM_TOKEN = '6200473625:AAHQggdvC2pXpATubj8COR7ogmP_y5-GRBc'

# Bybit API credentials
BYBIT_API_KEY = "your_bybit_api_key"
BYBIT_API_SECRET = "your_bybit_api_secret"

# PostgreSQL Database credentials
DB_NAME = "your_db_name"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_HOST = "your_db_host"
DB_PORT = "your_db_port"

# Global variables
trade_flag = False

# Initialize Bybit client
bybit_client = HTTP(api_key=BYBIT_API_KEY, api_secret=BYBIT_API_SECRET)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def create_signals_table():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            date TIMESTAMP,
            symbol TEXT,
            action TEXT,
            volume_percent NUMERIC,
            expiration TIMESTAMP
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()

# Command handlers
def start_command(update: Update, context: CallbackContext):
    global trade_flag
    trade_flag = True
    update.message.reply_text(f"Trading flag set to: {trade_flag}")

def stop_command(update: Update, context: CallbackContext):
    global trade_flag
    trade_flag = False
    update.message.reply_text(f"Trading flag set to: {trade_flag}")

def list_command(update: Update, context: CallbackContext):
    try:
        # Fetch account balance
        balance = bybit_client.get_wallet_balance(account_type="SPOT")
        balances = "\n".join([f"{key}: {value['availableBalance']}" for key, value in balance['result'].items()])

        # Fetch open positions
        positions = bybit_client.get_open_positions()
        positions_list = "\n".join([
            f"Date: {datetime.now()}, Symbol: {pos['symbol']}, Action: {pos['side']}, Volume: {pos['size']}, TP: {pos['takeProfit']}, SL: {pos['stopLoss']}"
            for pos in positions['result']
        ])

        # Fetch signals from DB
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM signals")
        signals = cursor.fetchall()
        signals_list = "\n".join([
            f"Date: {row[1]}, Symbol: {row[2]}, Action: {row[3]}, Expiration: {row[4]}"
            for row in signals
        ])
        cursor.close()
        connection.close()

        update.message.reply_text(f"**Balances:**\n{balances}\n\n**Open Positions:**\n{positions_list}\n\n**Signals:**\n{signals_list}")
    except Exception as e:
        update.message.reply_text(f"Error fetching data: {e}")

def trade_command(update: Update, context: CallbackContext):
    try:
        args = update.message.text.split()
        if len(args) != 3:
            update.message.reply_text("Invalid format. Use: /buy (or /sell) [symbol] [volume_percent]")
            return

        action = args[0][1:]
        symbol = args[1].upper()
        volume_percent = float(args[2])

        # Save signal to DB
        expiration = datetime.now() + timedelta(minutes=5)
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO signals (date, symbol, action, volume_percent, expiration) VALUES (%s, %s, %s, %s, %s)",
            (datetime.now(), symbol, action, volume_percent, expiration)
        )
        connection.commit()
        cursor.close()
        connection.close()

        update.message.reply_text(f"Signal created: {action.upper()} {symbol} with {volume_percent}% volume, expires at {expiration}")
    except Exception as e:
        update.message.reply_text(f"Error processing trade command: {e}")

def test_command(update: Update, context: CallbackContext):
    try:
        # Example: Fetch historical data for BTCUSDT
        symbol = "BTCUSDT"
        interval = "1m"
        limit = 200
        historical_data = bybit_client.get_kline(symbol=symbol, interval=interval, limit=limit)
        update.message.reply_text(f"Fetched {len(historical_data['result'])} candles for {symbol}")
    except Exception as e:
        update.message.reply_text(f"Error fetching historical data: {e}")

def handle_message(update: Update, context: CallbackContext):
    update.message.reply_text("Unrecognized command. Use /start, /stop, /list, /buy, /sell, or /test.")

# Main function
def main():
    create_signals_table()

    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("stop", stop_command))
    dp.add_handler(CommandHandler("list", list_command))
    dp.add_handler(CommandHandler("buy", trade_command))
    dp.add_handler(CommandHandler("sell", trade_command))
    dp.add_handler(CommandHandler("test", test_command))
    # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
