import time
import datetime
import threading
from pybit.unified_trading import HTTP
from telegram import Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters

# =========================== НАСТРОЙКИ ===========================
PERIOD_CHECK = 60  # период проверки в секундах
TRADING_ACTIVE = False
SIGNAL_LIFETIME = 300  # в секундах (5 минут)

TRADED_SYMBOLS = [
    {'symbol': 'BTCUSDT', 'deal_share': 0.1, 'stop_loss_share': 0.05, 'take_profit_share': 0.05}
]

SIGNAL_SOURCES = [
    {'source': 'TB', 'confidence': 0.6}
]

# =========================== API НАСТРОЙКИ ===========================
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
TG_TOKEN = 'your_telegram_token'
CHAT_ID = 'your_chat_id'

# =========================== ДАННЫЕ ===========================
SIGNALS = []  # Сигналы
POSITIONS = []  # Сделки
QUOTES = []  # Котировки

# =========================== ПОДКЛЮЧЕНИЕ ===========================
client = HTTP(api_key=API_KEY, api_secret=API_SECRET)
telegram_bot = Bot(token=TG_TOKEN)

# =========================== ФУНКЦИИ ===========================

# Функция отправки сообщений в Telegram
def send_telegram_message(message):
    telegram_bot.send_message(chat_id=CHAT_ID, text=message)

# Проверка сигналов и открытие позиций
def check_signals():
    global TRADING_ACTIVE

    while True:
        if not TRADING_ACTIVE:
            time.sleep(PERIOD_CHECK)
            continue

        # Удаление устаревших сигналов
        current_time = datetime.datetime.now()
        SIGNALS[:] = [s for s in SIGNALS if s['expire_time'] > current_time]

        # Проверка сигналов по символам
        for symbol in TRADED_SYMBOLS:
            symbol_signals = [s for s in SIGNALS if s['symbol'] == symbol['symbol']]
            signal_sum = sum(s['action'] * SIGNAL_SOURCES[0]['confidence'] for s in symbol_signals)

            if signal_sum > 1:
                open_position(symbol, 'long')
            elif signal_sum < -1:
                open_position(symbol, 'short')

        time.sleep(PERIOD_CHECK)

# Открытие позиции
def open_position(symbol, direction):
    deal_size = get_balance() * symbol['deal_share']
    price = get_price(symbol['symbol'])

    if direction == 'long':
        stop_loss = price - deal_size * symbol['stop_loss_share']
        take_profit = price + deal_size * symbol['take_profit_share']
    else:
        stop_loss = price + deal_size * symbol['stop_loss_share']
        take_profit = price - deal_size * symbol['take_profit_share']

    # Открытие сделки
    client.place_order(
        category="linear",
        symbol=symbol['symbol'],
        side='Buy' if direction == 'long' else 'Sell',
        orderType='Market',
        qty=deal_size,
        takeProfit=take_profit,
        stopLoss=stop_loss
    )
    send_telegram_message(f"Открыта позиция {direction.upper()} для {symbol['symbol']}")

# Получение текущего баланса
def get_balance():
    balance = client.get_wallet_balance(accountType='UNIFIED')
    return balance['result']['list'][0]['totalEquity']

# Получение текущей цены
def get_price(symbol):
    ticker = client.get_ticker(symbol=symbol)
    return float(ticker['result'][0]['lastPrice'])

# =========================== ТЕЛЕГРАМ-КОМАНДЫ ===========================

def start_command(update: Update, context: CallbackContext):
    global TRADING_ACTIVE
    TRADING_ACTIVE = True
    update.message.reply_text("Торговля запущена.")


def stop_command(update: Update, context: CallbackContext):
    global TRADING_ACTIVE
    TRADING_ACTIVE = False
    update.message.reply_text("Торговля остановлена.")


def list_command(update: Update, context: CallbackContext):
    balance = get_balance()
    update.message.reply_text(f"Баланс: {balance}")
    # Вывод открытых позиций
    positions = client.get_positions(category='linear')
    message = "Открытые позиции:\n"
    for pos in positions['result']['list']:
        message += f"{pos['symbol']} {pos['side']} Объем: {pos['size']} TP: {pos['takeProfit']} SL: {pos['stopLoss']}\n"
    update.message.reply_text(message)


def signal_command(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        update.message.reply_text("Неверный формат команды.")
        return

    action = 1 if args[0].lower() == 'buy' else -1
    source = 'TB'
    symbol = args[1].upper()

    # Проверка символа
    if not any(s['symbol'] == symbol for s in TRADED_SYMBOLS):
        update.message.reply_text("Символ не найден.")
        return

    SIGNALS.append({
        'date': datetime.datetime.now(),
        'source': source,
        'symbol': symbol,
        'action': action,
        'expire_time': datetime.datetime.now() + datetime.timedelta(seconds=SIGNAL_LIFETIME)
    })
    update.message.reply_text(f"Сигнал добавлен: {symbol} {args[0].upper()}")


def close_command(update: Update, context: CallbackContext):
    client.close_position(category='linear')
    update.message.reply_text("Все позиции закрыты.")

# =========================== ЗАПУСК ===========================
updater = Updater(TG_TOKEN)
dp = updater.dispatcher
dp.add_handler(CommandHandler('start', start_command))
dp.add_handler(CommandHandler('stop', stop_command))
dp.add_handler(CommandHandler('list', list_command))
dp.add_handler(CommandHandler('signal', signal_command, pass_args=True))
dp.add_handler(CommandHandler('close', close_command))

threading.Thread(target=check_signals).start()
updater.start_polling()
updater.idle()
