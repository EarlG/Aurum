import time

def data_collector(stop_flag):
    """Модуль для сбора данных."""
    print("[data_collector] Модуль запущен")
    try:
        while not stop_flag.is_set():
            # Здесь может быть ваша логика сбора данных, например, из API
            print("[data_collector] Сбор данных...")
            time.sleep(5)  # Интервал выполнения
    except Exception as e:
        print(f"[data_collector] Ошибка: {e}")
    finally:
        print("[data_collector] Модуль остановлен")
