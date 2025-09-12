import sqlite3
from typing import List, Tuple


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect('sleepbot.db')


def create_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    # Core tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sleep_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sleep_time TEXT NOT NULL,
        wake_time TEXT NOT NULL,
        date TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement TEXT NOT NULL
    )
    ''')

    # Constraints and indexes
    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_sleep_unique_user_date
    ON sleep_data(user_id, date)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_sleep_user
    ON sleep_data(user_id)
    ''')

    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_achievements_unique
    ON achievements(user_id, achievement)
    ''')

    conn.commit()
    conn.close()


def insert_sleep_data(user_id: int, sleep_time: str, wake_time: str, date: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    # Use INSERT OR REPLACE to respect unique(user_id, date) and update existing row
    cursor.execute('''
    INSERT INTO sleep_data (user_id, sleep_time, wake_time, date)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, date) DO UPDATE SET
        sleep_time=excluded.sleep_time,
        wake_time=excluded.wake_time
    ''', (user_id, sleep_time, wake_time, date))
    conn.commit()
    conn.close()


def get_sleep_data(user_id: int) -> List[Tuple[str, str, str]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT sleep_time, wake_time, date
    FROM sleep_data
    WHERE user_id = ?
    ORDER BY date ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def insert_achievement(user_id: int, achievement: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO achievements (user_id, achievement)
    VALUES (?, ?)
    ''', (user_id, achievement))
    conn.commit()
    conn.close()


def get_achievements(user_id: int) -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT achievement FROM achievements
    WHERE user_id = ?
    ORDER BY achievement ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


# Ensure tables exist on import
create_tables()