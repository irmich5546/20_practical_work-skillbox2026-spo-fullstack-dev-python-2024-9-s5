import sqlite3
from datetime import datetime

DB_NAME = "rates.db"

def init_db():
    """Инициализация БД. Создайте таблицу со столбцами: id, имя валюты, курс, дата обновления"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY,
            currency TEXT UNIQUE,
            rate REAL,
            fetched_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_rate(id: int, target_currency: str, rate: float):
    """Сохранение данных о курсе валют в БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_str = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO rates (id, currency, rate, fetched_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            rate = excluded.rate,
            fetched_at = excluded.fetched_at
    """, (id, target_currency, rate, date_str))
    conn.commit()
    conn.close()

def get_saved_rate(target_currency: str) -> float:
    """Получение курса по имени валюты из БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM rates WHERE currency = ?", (target_currency,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0.0