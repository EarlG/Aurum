import time
import logging
from datetime import datetime, timedelta

# https://habr.com/ru/companies/otus/articles/771110/
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from pybit.unified_trading import HTTP

# ---------------- НАСТРОЙКИ ----------------
CHECK_INTERVAL = 60  # Период проверки в секундах (1 минута)
TRADE_FLAG = False  # Флаг запуска торговли
SIGNAL_LIFETIME = 300  # Время жизни сигнала в секундах (5 минут)

TRADE_SYMBOLS = [
    {'symbol': 'BTCUSDT', 'deal_size': 0.1, 'stop_loss': 0.05, 'take_profit': 0.05},
    {'symbol': 'ETHUSDT', 'deal_size': 0.1, 'stop_loss': 0.05, 'take_profit': 0.05},
]

SIGNAL_SOURCES = [
    {'source': 'TB', 'trust_factor': 0.6}
]

# Переменные
signals = []  # Сигналы
trades = []  # Сделки
quotes = []  # Котировки

# Настройки API Bybit
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'

# Telegram Token
TELEGRAM_TOKEN = 'your_telegram_token'

# ---------------- ЛОГИРОВАНИЕ ----------------
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- API Bybit ----------------
session = HTTP(api_key=API_KEY, api_secret=API_SECRET)


# ---------------- ФУНКЦИИ ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TRADE_FLAG
    TRADE_FLAG = True
    await update.message.reply_text(f"Торговля запущена: {TRADE_FLAG}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TRADE_FLAG
    TRADE_FLAG = False
    await update.message.reply_text(f"Торговля остановлена: {TRADE_FLAG}")


async def list_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Депозит
    balance = session.get_wallet_balance(accountType='UNIFIED')
    await update.message.reply_text(f"Текущий баланс: {balance['result']['totalEquity']}")

    # Открытые позиции
    positions = session.get_positions()
    position_list = '\n'.join([
        f"{p['symbol']} {p['side']} {p['size']} SL: {p['stopLoss']} TP: {p['takeProfit']}"
        for p in positions['result']['list']
    ])
    await update.message.reply_text(f"Позиции:\n{position_list}")

    # Сигналы
    signals_list = '\n'.join([
        f"{s['date']} {s['symbol']} {s['action']} до {s['expiry']}"
        for s in signals
    ])
    await update.message.reply_text(f"Сигналы:\n{signals_list}")


async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TRADE_FLAG
    positions = session.get_positions()
    for p in positions['result']['list']:
        session.close_position(symbol=p['symbol'], side=p['side'])
    TRADE_FLAG = False
    await update.message.reply_text("Все позиции закрыты. Торговля остановлена.")


async def buy_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Некорректная команда. Пример: buy btcusdt")
        return

    action = args[0].lower()
    symbol = args[1].upper()
    source = 'TB'

    if len(args) > 2:
        source = args[2]

    if action not in ['buy', 'sell']:
        await update.message.reply_text("Некорректное действие. Используйте buy или sell.")
        return

    # Проверяем символ
    if symbol not in [s['symbol'] for s in TRADE_SYMBOLS]:
        await update.message.reply_text("Символ не найден в торгуемых символах.")
        return

    # Добавляем сигнал
    signals.append({
        'date': datetime.now(),
        'source': source,
        'symbol': symbol,
        'action': 1 if action == 'buy' else -1,
        'expiry': datetime.now() + timedelta(seconds=SIGNAL_LIFETIME)
    })
    await update.message.reply_text(f"Добавлен сигнал: {action.upper()} {symbol}")


async def trading_logic():
    global TRADE_FLAG
    while True:
        if not TRADE_FLAG:
            await asyncio.sleep(CHECK_INTERVAL)
            continue

        # Удаление истекших сигналов
        now = datetime.now()
        signals[:] = [s for s in signals if s['expiry'] > now]

        # Обработка сигналов
        for trade_symbol in TRADE_SYMBOLS:
            symbol = trade_symbol['symbol']
            total_signal = sum(
                source['trust_factor'] * s['action']
                for s in signals
                for source in SIGNAL_SOURCES
                if s['symbol'] == symbol and s['source'] == source['source']
            )

            # Логика открытия позиции
            if total_signal > 1:
                # Лонг
                open_position(symbol, 'Buy', trade_symbol)
            elif total_signal < -1:
                # Шорт
                open_position(symbol, 'Sell', trade_symbol)

        await asyncio.sleep(CHECK_INTERVAL)


def open_position(symbol, side, trade_symbol):
    price = float(session.get_ticker(symbol=symbol)['result'][0]['lastPrice'])
    deal_size = 0.1 * price

    sl = price - deal_size * trade_symbol['stop_loss'] if side == 'Buy' else price + deal_size * trade_symbol['stop_loss']
    tp = price + deal_size * trade_symbol['take_profit'] if side == 'Buy' else price - deal_size * trade_symbol['take_profit']

    session.place_order(
        symbol=symbol, side=side, orderType='Market', qty=deal_size,
        stopLoss=str(sl), takeProfit=str(tp)
    )


# ---------------- ЗАПУСК ----------------
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("list", list_data))
app.add_handler(CommandHandler("close", close))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buy_sell))

app.run_polling()
asyncio.run(trading_logic())