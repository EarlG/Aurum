import psycopg2
import threading
import time
from datetime import datetime

# --- Настройки подключения к БД ---
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "1234567",
    "host": "localhost",
    "port": 5432,
}

# --- Глобальные переменные ---
GLOBAL_SETTINGS = {}


# --- Функция для чтения настроек из БД ---
def load_settings_from_db():
    global GLOBAL_SETTINGS
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Извлекаем все настройки
    cur.execute("SELECT key, value, type FROM aurum.settings")
    rows = cur.fetchall()

    # Преобразуем значения на основе типа
    settings = {}
    for key, value, value_type in rows:
        if value_type == "integer":
            settings[key] = int(value)
        elif value_type == "boolean":
            settings[key] = value.lower() == "true"
        elif value_type == "json":
            import json
            settings[key] = json.loads(value)
        else:  # По умолчанию строка
            settings[key] = value

    GLOBAL_SETTINGS = settings
    cur.close()
    conn.close()
    print(f"[{datetime.now()}] Настройки обновлены: {GLOBAL_SETTINGS}")


# --- Функция для периодического обновления настроек ---
def periodic_settings_update(interval=60):
    while True:
        try:
            load_settings_from_db()
        except Exception as e:
            print(f"Ошибка при обновлении настроек: {e}")
        time.sleep(interval)


# --- Запуск обновления настроек в отдельном потоке ---
def start_settings_updater(interval=60):
    updater_thread = threading.Thread(target=periodic_settings_update, args=(interval,))
    updater_thread.daemon = True
    updater_thread.start()


# --- Пример использования ---
if __name__ == "__main__":
    # Стартуем процесс обновления настроек
    start_settings_updater(interval=30)  # Обновлять настройки каждые 30 секунд

    # Пример использования настроек в основной программе
    while True:
        if "trade_flag" in GLOBAL_SETTINGS:
            trade_flag = GLOBAL_SETTINGS["trade_flag"]
            print(f"Текущий флаг торговли: {trade_flag}")
        else:
            print("Настройка trade_flag отсутствует.")

        time.sleep(10)
