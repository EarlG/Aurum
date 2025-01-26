import psycopg2
from psycopg2 import sql
from datetime import datetime
from pybit.unified_trading import HTTP

from au_logger import AsyncDatabaseLogger

# Настройки базы данных
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "1234567",
    "host": "localhost",
    "port": 5432,
}

logger = AsyncDatabaseLogger(DB_CONFIG, source="collect_quotes_001")

# Настройки Bybit API
#BYBIT_API_KEY = "your_api_key"
#BYBIT_API_SECRET = "your_api_secret"
BYBIT_API_KEY = "Pr7cgsl9xCvBLMqptR"
BYBIT_API_SECRET = "yaAAqi6ry9Sm7lzIzl7sQECMA23DYMY0fujkI"

# Инициализация клиента Bybit
#bybit_client = HTTP(
#    testnet=True,  # Установите в False для реальной торговли
#    api_key=BYBIT_API_KEY,
#    api_secret=BYBIT_API_SECRET,
#)

bybit_client = HTTP(testnet=True)

# Получение исторических котировок
def get_historical_quotes(symbol: str, interval: str, start_time: int, limit: int = 20000):
    """
    Получает исторические данные по символу с Bybit API.
    :param symbol: Торговый символ (например, BTCUSDT)
    :param interval: Интервал свечей (например, 1m, 5m, 1h)
    :param start_time: Начальное время в формате Unix Timestamp
    :param limit: Количество свечей (по умолчанию 200)
    :return: Список свечей
    """
    response = bybit_client.get_kline(
        category="linear",
        symbol=symbol,
        interval=interval,
        start=start_time,
        limit=limit,
    )

    logger.log("INFO", "bybit_client.get_kline", details=response)

    if response["retCode"] != 0:
        raise Exception(f"Ошибка получения данных Bybit: {response['retMsg']}")
    return response["result"]["list"]

# Запись котировок в PostgreSQL
def insert_quotes_into_db(quotes, symbol, interval):
    """
    Записывает данные котировок в таблицу quotes базы данных PostgreSQL.
    :param quotes: Список котировок
    :param symbol: Торговый символ
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    insert_query = sql.SQL("""
        INSERT INTO aurum.quotes (
            symbol, quote_date, open_price, high_price, low_price, close_price, volume, interval, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT DO NOTHING;
        
    CREATE TABLE IF NOT EXISTS aurum.quotes (
    id SERIAL PRIMARY KEY,                     -- Уникальный идентификатор записи
    symbol VARCHAR(20) NOT NULL,               -- Торговый символ (например, BTCUSD)
    quote_date TIMESTAMP NOT NULL,             -- Дата и время котировки
    open_price NUMERIC(18, 8),        -- Цена открытия
    high_price NUMERIC(18, 8),        -- Максимальная цена
    low_price NUMERIC(18, 8),         -- Минимальная цена
    close_price NUMERIC(18, 8) NOT NULL,       -- Цена закрытия
    volume NUMERIC(18, 8),            -- Объем торгов
    interval VARCHAR(10) NOT NULL,             -- Интервал свечи (например, 1m, 5m, 1h)
    created_at TIMESTAMP DEFAULT NOW(),        -- Время создания записи
    UNIQUE (symbol, quote_date, interval)      -- Уникальный ключ для предотвращения дублирования
    );
    """)

    for quote in quotes:
        quote_date = datetime.fromtimestamp(int(quote[0]) / 1000)
        open_price = float(quote[1])
        high_price = float(quote[2])
        low_price = float(quote[3])
        close_price = float(quote[4])
        volume = float(quote[5])

        cursor.execute(
            insert_query,
            (symbol, quote_date, open_price, high_price, low_price, close_price, volume, interval)
        )

    conn.commit()
    cursor.close()
    conn.close()

# Основная функция
def main():
    symbol = "BTCUSD"  # Торговый символ
    interval = "60"  # Интервал свечей (например, 1m, 5m, 1h) Kline interval. 1,3,5,15,30,60,120,240,360,720,D,M,W
    start_time = int(datetime(2025, 1, 2).timestamp() * 1000)  # Начальная дата в формате Unix Timestamp (мс)

    try:
        print(f"Получение данных для символа {symbol}...")
        quotes = get_historical_quotes(symbol, interval, start_time)
        print(f"Получено {len(quotes)} записей. Запись в базу данных...")
        insert_quotes_into_db(quotes, symbol, interval)
        print("Запись завершена.")
    except Exception as e:
        print(f"Ошибка1: {e}")

if __name__ == "__main__":
    main()
    logger.stop()