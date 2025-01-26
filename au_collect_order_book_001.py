import psycopg2
from psycopg2 import sql
from datetime import datetime
from pybit.unified_trading import HTTP
import time

from au_logger import AsyncDatabaseLogger



# Настройки базы данных
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "1234567",
    "host": "localhost",
    "port": 5432,
}

# Настройки Bybit API
BYBIT_API_KEY = "your_api_key"
BYBIT_API_SECRET = "your_api_secret"
SYMBOL = "BTCUSD"  # Торговый символ
BYBIT_API_URL = "https://api.bybit.com"

# Инициализация клиента Bybit
bybit_client = HTTP(
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
    testnet=True  # Установите False для реального рынка
)

def get_order_book(symbol):
    """
    Получение стакана цен с API Bybit.
    :param symbol: Торговый символ
    :return: Словарь со стаканом цен (bids и asks)
    """
    response = bybit_client.get_orderbook(
        category="linear",
        symbol=symbol
    )

    if response["retCode"] != 0:
        raise Exception(f"Ошибка API Bybit: {response['retMsg']}")

    return response["result"]

def save_order_book_history_to_db(order_book, symbol):
    """
    Сохранение истории стакана цен в базу данных PostgreSQL.
    :param order_book: Словарь со стаканом цен (bids и asks)
    :param symbol: Торговый символ
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # SQL-запрос для вставки данных
    insert_query = sql.SQL("""
        INSERT INTO aurum.order_book_history (
            symbol, price, quantity, side, created_at
        ) VALUES (%s, %s, %s, %s, NOW());
    """)

    # Сохранение bid уровней
    for bid in order_book["b"]:
        price, quantity = float(bid[0]), float(bid[1])
        cursor.execute(insert_query, (symbol, price, quantity, "buy"))

    # Сохранение ask уровней
    for ask in order_book["a"]:
        price, quantity = float(ask[0]), float(ask[1])
        cursor.execute(insert_query, (symbol, price, quantity, "sell"))

    conn.commit()
    cursor.close()
    conn.close()

def main():
    """
    Основная функция для постоянного получения стакана цен и сохранения в базу данных.
    """
    #logger = AsyncDatabaseLogger(DB_CONFIG, source="au_collect_order_book_001")
    print(f"Запуск программы для символа {SYMBOL}. Нажмите Ctrl+C для выхода.")
    while True:
        try:
            # Получение стакана цен
            order_book = get_order_book(SYMBOL)

            # Сохранение стакана в базу данных
            save_order_book_history_to_db(order_book, SYMBOL)
            print(f"Стакан цен для {SYMBOL} сохранен в базу данных ({datetime.now()}).")
         #   logger.log("INFO", f"Стакан цен для {SYMBOL} сохранен в базу данных ({datetime.now()}).")
            # Задержка перед следующим запросом
            time.sleep(1)

        except KeyboardInterrupt:
            print("Программа остановлена пользователем.")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
