
"""

CREATE TABLE aurum.settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    group_name VARCHAR(255) DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS aurum.quotes (
    id SERIAL PRIMARY KEY,                     -- Уникальный идентификатор записи
    symbol VARCHAR(50) NOT NULL,               -- Торговый символ (например, BTCUSD)
    quote_date TIMESTAMP NOT NULL,             -- Дата и время котировки
    open_price NUMERIC(18, 8) NOT NULL,        -- Цена открытия
    high_price NUMERIC(18, 8) NOT NULL,        -- Максимальная цена
    low_price NUMERIC(18, 8) NOT NULL,         -- Минимальная цена
    close_price NUMERIC(18, 8) NOT NULL,       -- Цена закрытия
    volume NUMERIC(18, 8) NOT NULL,            -- Объем торгов
    interval VARCHAR(10) NOT NULL,             -- Интервал свечи (например, 1m, 5m, 1h)
    created_at TIMESTAMP DEFAULT NOW(),        -- Время создания записи
    UNIQUE (symbol, quote_date, interval)      -- Уникальный ключ для предотвращения дублирования
);

CREATE TABLE good_trades_dataset (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    trade_side VARCHAR(10) CHECK (trade_type IN ('long', 'short')),
    open_date TIMESTAMP NOT NULL,
    close_date TIMESTAMP NOT NULL,
    open_price DECIMAL(18, 8) NOT NULL,
    close_price DECIMAL(18, 8) NOT NULL,
    profit DECIMAL(18, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Время создания записи
);

CREATE TABLE trades (
    id SERIAL PRIMARY KEY, -- Уникальный идентификатор сделки
    symbol VARCHAR(20) NOT NULL, -- Символ инструмента (например, BTCUSDT)
    trade_date TIMESTAMP NOT NULL, -- Дата и время сделки
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short'))
    quantity DECIMAL(18, 8) NOT NULL, -- Количество
    price DECIMAL(18, 8) NOT NULL, -- Цена исполнения
    leverage INTEGER NOT NULL, -- Используемое плечо
    stop_loss DECIMAL(18, 8), -- Стоп-лосс
    take_profit DECIMAL(18, 8), -- Тейк-профит
    status VARCHAR(20) NOT NULL CHECK (status IN ('open', 'closed', 'canceled')), -- Статус сделки (open, closed, canceled)
    pnl DECIMAL(18, 8) DEFAULT 0.00, -- Прибыль/убыток
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Время создания записи
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Время последнего обновления
);


CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY, -- Уникальный идентификатор сигнала
    signal_date TIMESTAMP NOT NULL, -- Дата и время создания сигнала
    source VARCHAR(50) NOT NULL, -- Источник сигнала (например, TelegramBot, TradingView)
    symbol VARCHAR(20) NOT NULL, -- Символ инструмента (например, BTCUSDT)
    action VARCHAR(10) NOT NULL CHECK (action IN ('buy', 'sell', 'long', 'short', 'flat')), -- Действие (buy, sell, long, short, flat)
    expiration_date TIMESTAMP NOT NULL, -- Дата окончания действия сигнала
    confidence_level DECIMAL(5, 2) DEFAULT 1.00, -- Уровень доверия к сигналу
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Время создания записи
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Время последнего обновления




"""