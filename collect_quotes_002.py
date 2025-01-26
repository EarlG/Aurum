import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta

# Конфигурация подключения к базе данных PostgreSQL
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "1234567",
    "host": "localhost",
    "port": 5432,
}

# Конфигурация API Bybit
BYBIT_API_URL = "https://api-testnet.bybit.com"
SYMBOL = "BTCUSDT"
INTERVAL = "1"  # Интервал свечей: "1", "3", "5", "15", "30", "60", "240", "D", "W", "M"
LIMIT = 200  # Максимальное количество свечей за один запрос (200)


def get_historical_data(symbol, interval, from_time):
    """
    Получение исторических данных по символу с API Bybit.

    :param symbol: Символ торговой пары (например, "BTCUSDT").
    :param interval: Интервал свечей (например, "1" для 1 минуты).
    :param from_time: UNIX-время начала запрашиваемого периода.
    :return: Список свечей с данными.
    """
    endpoint = f"{BYBIT_API_URL}/v2/public/kline/list"
    params = {
        "symbol": symbol,
        "interval": interval,
        "from": from_time,
        "limit": LIMIT
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    data = response.json()

    if data["ret_code"] == 0:
        return data["result"]
    else:
        raise Exception(f"Ошибка API Bybit: {data['ret_msg']}")


def save_to_database(data, db_config):
    """
    Сохранение данных в таблицу quotes в базе данных PostgreSQL.

    :param data: Список свечей с данными.
    :param db_config: Конфигурация подключения к базе данных.
    """
    connection = psycopg2.connect(**db_config)
    cursor = connection.cursor()

    # SQL-запрос для вставки данных
    insert_query = """
        INSERT INTO aurum.quotes (
            symbol, quote_date, open_price, high_price, low_price, close_price, volume, interval
        ) VALUES %s
        ON CONFLICT (symbol, quote_date) DO NOTHING
    """

    # Подготовка данных для вставки
    values = [
        (
            SYMBOL,
            datetime.fromtimestamp(int(candle["open_time"])),
            float(candle["open"]),
            float(candle["high"]),
            float(candle["low"]),
            float(candle["close"]),
            float(candle["volume"]),
            INTERVAL  # Добавление интервала
        )
        for candle in data
    ]

    # Вставка данных
    execute_values(cursor, insert_query, values)
    connection.commit()

    cursor.close()
    connection.close()


def fetch_and_save_historical_data(start_time, end_time, db_config):
    """
    Получение исторических данных с API Bybit и сохранение их в базу данных.

    :param start_time: Время начала периода (datetime).
    :param end_time: Время окончания периода (datetime).
    :param db_config: Конфигурация подключения к базе данных.
    """
    current_time = start_time
    while current_time < end_time:
        from_time = int(current_time.timestamp())
        print(f"Получение данных с {current_time}...")

        try:
            data = get_historical_data(SYMBOL, INTERVAL, from_time)
            if not data:
                print("Нет данных для указанного периода.")
                break

            save_to_database(data, db_config)
            print(f"Данные с {current_time} успешно сохранены в базу данных.")

            # Обновление времени для следующего запроса
            current_time += timedelta(minutes=LIMIT)

        except Exception as e:
            print(f"Ошибка: {e}")
            break


if __name__ == "__main__":
    # Период для загрузки данных
    start_time = datetime.now() - timedelta(days=7)  # Последние 7 дней
    end_time = datetime.now()

    # Получение и сохранение исторических данных
    fetch_and_save_historical_data(start_time, end_time, DB_CONFIG)