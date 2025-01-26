from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pybit.unified_trading import HTTP
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
trade_flag = False
signals = []  # Example signal list, should be connected to your database or file
bybit_api_key = "your_api_key"
bybit_api_secret = "your_api_secret"
bybit_session = HTTP(api_key=bybit_api_key, api_secret=bybit_api_secret)

# Define command handlers
async def start(update: Update, context: CallbackContext):
    global trade_flag
    trade_flag = True
    await update.message.reply_text(f"Trading started. Trade flag: {trade_flag}")

async def stop(update: Update, context: CallbackContext):
    global trade_flag
    trade_flag = False
    await update.message.reply_text(f"Trading stopped. Trade flag: {trade_flag}")

async def list(update: Update, context: CallbackContext):
    try:
        # Get account balance
        balance = bybit_session.get_wallet_balance(accountType="SPOT")
        balance_msg = f"Current Balance: {json.dumps(balance, indent=2)}"

        # Get open positions
        positions = bybit_session.get_positions()
        positions_msg = "Open Positions:\n"
        for pos in positions['result']:
            positions_msg += (f"Date: {pos['updatedTime']}, Symbol: {pos['symbol']}, Action: {pos['side']}, "
                              f"Volume: {pos['size']}, TP: {pos['takeProfit']}, SL: {pos['stopLoss']}\n")

        # Get signals
        signals_msg = "Trading Signals:\n"
        for signal in signals:
            signals_msg += (f"Date: {signal['date']}, Symbol: {signal['symbol']}, Action: {signal['action']}, "
                            f"Valid Until: {signal['valid_until']}\n")

        await update.message.reply_text(f"{balance_msg}\n\n{positions_msg}\n\n{signals_msg}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching data: {e}")

async def buy_sell(update: Update, context: CallbackContext):
    try:
        command = update.message.text.split()
        action, symbol, volume_percentage = command[0], command[1], float(command[2])

        # Get account balance
        balance = bybit_session.get_wallet_balance(accountType="SPOT")
        usdt_balance = balance['result']['spot']['availableBalance']
        volume = (usdt_balance * volume_percentage) / 100

        # Place order
        order = bybit_session.place_active_order(
            symbol=symbol,
            side="Buy" if action.lower() == "buy" else "Sell",
            order_type="Market",
            qty=volume,
            time_in_force="GoodTillCancel"
        )

        await update.message.reply_text(f"Order placed: {json.dumps(order, indent=2)}")
        await list(update, context)

    except Exception as e:
        await update.message.reply_text(f"Error processing command: {e}")

async def test(update: Update, context: CallbackContext):
    try:
        symbol = "BTCUSDT"  # Default symbol for testing
        historical_data = bybit_session.query_kline(
            symbol=symbol,
            interval="1",  # 1 minute interval
            limit=200
        )
        await update.message.reply_text(f"Historical Data:\n{json.dumps(historical_data, indent=2)}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching historical data: {e}")

async def message_handler(update: Update, context: CallbackContext):
    text = update.message.text.lower()
    if text.startswith("buy") or text.startswith("sell"):
        await buy_sell(update, context)
    elif text == "start":
        await start(update, context)
    elif text == "stop":
        await stop(update, context)
    elif text == "list":
        await list(update, context)
    elif text == "test":
        await test(update, context)
    else:
        await update.message.reply_text(f"OK {text}")

# Main function
def main():
    telegram_token = '6200473625:AAHQggdvC2pXpATubj8COR7ogmP_y5-GRBc'
    application = Application.builder().token(telegram_token).build()

    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
