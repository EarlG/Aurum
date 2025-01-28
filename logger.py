import time

def logger():
    """Модуль для логирования."""
    print("[logger] Модуль запущен")
    try:
        while True:
            # Логика записи в лог-файл
            with open("module_logs.txt", "a") as f:
                f.write("[logger] Запись лога...\n")
            print("[logger] Лог записан")
            time.sleep(5)  # Интервал выполнения
    except KeyboardInterrupt:
        print("[logger] Модуль остановлен")
