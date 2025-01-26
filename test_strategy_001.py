import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pybit.unified_trading import HTTP

# Настройки API Bybit
BYBIT_API_KEY = "Pr7cgsl9xCvBLMqptR"
BYBIT_API_SECRET = "yaAAqi6ry9Sm7lzIzl7sQECMA23DYMY0fujkI"
# BYBIT_API_SECRET = "test"
SYMBOL = "BTCUSDT"
INTERVAL = "1h"  # Интервал свечей

# Параметры стратегии
SHORT_WINDOW = 7  # Период короткой скользящей средней
LONG_WINDOW = 25  # Период длинной скользящей средней
TRADE_FEE_PERCENT = 0.075 / 100  # Торговая комиссия Bybit
INITIAL_BALANCE = 10000  # Начальный баланс в USDT
LEVERAGE = 10  # Плечо

# Подключение к Bybit API
client = HTTP(
    testnet=True,  # Установите в False для реальной торговли
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
)

# Получение исторических данных
def fetch_historical_data(symbol, interval, limit=1000):
    response = client.get_kline(
        category="linear",
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    if response["retCode"] != 0:
        raise Exception(f"Ошибка получения данных: {response['ret_msg']}")
    data = pd.DataFrame(response["result"]["list"], columns=[
        "open_time", "open", "high", "low", "close", "volume", "turnover", "close_time", "quote_asset_volume", "trades"
    ])
    data["open_time"] = pd.to_datetime(data["open_time"], unit='ms')
    data["close"] = data["close"].astype(float)
    return data[["open_time", "close"]]

# Вычисление сигналов стратегии
def calculate_signals(data):
    data["SMA_SHORT"] = data["close"].rolling(window=SHORT_WINDOW).mean()
    data["SMA_LONG"] = data["close"].rolling(window=LONG_WINDOW).mean()
    data["signal"] = 0
    data.loc[data["SMA_SHORT"] > data["SMA_LONG"], "signal"] = 1  # Покупка
    data.loc[data["SMA_SHORT"] < data["SMA_LONG"], "signal"] = -1  # Продажа
    return data

# Тестирование стратегии
def backtest_strategy(data):
    balance = INITIAL_BALANCE
    position = None  # Текущая позиция (None, "long", "short")
    entry_price = 0
    pnl_history = []  # История баланса
    trade_log = []  # Лог сделок

    for i in range(len(data)):
        current_signal = data["signal"].iloc[i]
        current_price = data["close"].iloc[i]

        # Логика входа и выхода из позиций
        if position is None:  # Открытие позиции
            if current_signal == 1:  # Long
                position = "long"
                entry_price = current_price
                trade_log.append({"type": "long", "price": entry_price, "time": data["open_time"].iloc[i]})
            elif current_signal == -1:  # Short
                position = "short"
                entry_price = current_price
                trade_log.append({"type": "short", "price": entry_price, "time": data["open_time"].iloc[i]})

        elif position == "long" and current_signal == -1:  # Закрытие Long и открытие Short
            pnl = ((current_price - entry_price) / entry_price) * LEVERAGE * balance - TRADE_FEE_PERCENT * balance
            balance += pnl
            trade_log.append({"type": "close_long", "price": current_price, "time": data["open_time"].iloc[i], "pnl": pnl})
            position = "short"
            entry_price = current_price
            trade_log.append({"type": "short", "price": entry_price, "time": data["open_time"].iloc[i]})

        elif position == "short" and current_signal == 1:  # Закрытие Short и открытие Long
            pnl = ((entry_price - current_price) / entry_price) * LEVERAGE * balance - TRADE_FEE_PERCENT * balance
            balance += pnl
            trade_log.append({"type": "close_short", "price": current_price, "time": data["open_time"].iloc[i], "pnl": pnl})
            position = "long"
            entry_price = current_price
            trade_log.append({"type": "long", "price": entry_price, "time": data["open_time"].iloc[i]})

        # Сохранение истории баланса
        pnl_history.append(balance)

    # Закрытие открытой позиции в конце
    if position == "long":
        pnl = ((current_price - entry_price) / entry_price) * LEVERAGE * balance - TRADE_FEE_PERCENT * balance
        balance += pnl
        trade_log.append({"type": "close_long", "price": current_price, "time": data["open_time"].iloc[-1], "pnl": pnl})
    elif position == "short":
        pnl = ((entry_price - current_price) / entry_price) * LEVERAGE * balance - TRADE_FEE_PERCENT * balance
        balance += pnl
        trade_log.append({"type": "close_short", "price": current_price, "time": data["open_time"].iloc[-1], "pnl": pnl})

    return balance, trade_log, pnl_history

# Построение графика баланса
def plot_pnl_history(pnl_history):
    plt.figure(figsize=(12, 6))
    plt.plot(pnl_history, label="Баланс")
    plt.title("История изменения баланса")
    plt.xlabel("Шаги")
    plt.ylabel("Баланс (USDT)")
    plt.legend()
    plt.show()

# Основная функция
def main():
    # Загрузка данных
    print("Загрузка исторических данных...")
    data = fetch_historical_data(SYMBOL, INTERVAL, limit=1000)
    data = calculate_signals(data)

    # Тестирование стратегии
    print("Тестирование стратегии...")
    final_balance, trade_log, pnl_history = backtest_strategy(data)

    # Результаты
    print(f"Начальный баланс: {INITIAL_BALANCE} USDT")
    print(f"Итоговый баланс: {final_balance:.2f} USDT")
    print(f"Количество сделок: {len(trade_log)}")
    print(f"Сделки:")
    for trade in trade_log:
        print(trade)

    # Построение графика баланса
    plot_pnl_history(pnl_history)

if __name__ == "__main__":
    main()