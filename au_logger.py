import logging
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import threading
import queue

# Конфигурация подключения к базе данных PostgreSQL

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "1234567",
    "host": "localhost",
    "port": 5432,
}

class AsyncDatabaseLogger:
    def __init__(self, db_config, source):
        """
        Инициализация асинхронного логгера.

        :param db_config: Конфигурация базы данных.
        :param source: Источник логов (например, имя программы или модуля).
        """
        self.db_config = db_config
        self.source = source
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._log_worker, daemon=True)
        self.thread.start()

    def _log_worker(self):
        """
        Фоновый поток для записи логов в базу данных.
        """
        connection = psycopg2.connect(**self.db_config)
        cursor = connection.cursor()
        try:
            while not self.stop_event.is_set() or not self.log_queue.empty():
                try:
                    # Получение записи из очереди
                    log_entry = self.log_queue.get(timeout=1)
                    timestamp, level, source, message, details = log_entry

                    # Запись в базу данных
                    query = """
                        INSERT INTO aurum.logs (timestamp, level, source, message, details)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, (timestamp, level, source, message, Json(details)))
                    connection.commit()
                except queue.Empty:
                    continue
        except Exception as e:
            print(f"Ошибка в логировании: {e}")
        finally:
            cursor.close()
            connection.close()

    def log(self, level, message, details=None):
        """
        Добавляет запись в очередь логов.

        :param level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        :param message: Основное сообщение лога.
        :param details: Дополнительные данные (опционально, формат JSON).
        """
        timestamp = datetime.utcnow()
        self.log_queue.put((timestamp, level, self.source, message, details))

    def stop(self):
        """
        Останавливает поток логирования и дожидается завершения работы.
        """
        self.stop_event.set()
        self.thread.join()


# Пример использования
if __name__ == "__main__":
    # Инициализация логгера
    logger = AsyncDatabaseLogger(DB_CONFIG, source="TradingBot")

    try:
        # Логирование различных событий
        logger.log("INFO", "Программа торгового робота запущена.")

        # Эмуляция обработки сигнала
        signal = {"symbol": "BTCUSDT", "action": "BUY", "confidence": 0.9}
        logger.log("DEBUG", "Получен торговый сигнал.", details=signal)

        # Эмуляция успешного открытия позиции
        trade_result = {"symbol": "BTCUSDT", "size": 0.1, "entry_price": 30000}
        logger.log("INFO", "Позиция открыта успешно.", details=trade_result)

        # Эмуляция ошибки
        raise ValueError("Не удалось выполнить ордер.")

    except ValueError as e:
        logger.log("ERROR", "Ошибка при выполнении ордера.", details={"error": str(e)})

    finally:
        # Остановка логгера
        logger.stop()