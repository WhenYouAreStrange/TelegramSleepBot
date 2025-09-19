from telegram.ext import Application
import aiosqlite
from typing import List, Tuple

DB_FILE = 'sleepbot.db'


async def create_tables(_: Application) -> None:
    """Асинхронно создает таблицы в базе данных, если они не существуют."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS sleep_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sleep_time TEXT NOT NULL,
            wake_time TEXT NOT NULL,
            date TEXT NOT NULL
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement TEXT NOT NULL
        )
        ''')

        await db.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_sleep_unique_user_date
        ON sleep_data(user_id, date)
        ''')

        await db.execute('''
        CREATE INDEX IF NOT EXISTS idx_sleep_user
        ON sleep_data(user_id)
        ''')

        await db.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_achievements_unique
        ON achievements(user_id, achievement)
        ''')
        await db.commit()


async def insert_sleep_data(user_id: int, sleep_time: str, wake_time: str, date: str) -> None:
    """Асинхронно вставляет или обновляет данные о сне."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
        INSERT INTO sleep_data (user_id, sleep_time, wake_time, date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            sleep_time=excluded.sleep_time,
            wake_time=excluded.wake_time
        ''', (user_id, sleep_time, wake_time, date))
        await db.commit()


async def get_sleep_data(user_id: int) -> List[Tuple[str, str, str]]:
    """Асинхронно получает данные о сне пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
        SELECT sleep_time, wake_time, date
        FROM sleep_data
        WHERE user_id = ?
        ORDER BY date ASC
        ''', (user_id,))
        rows = await cursor.fetchall()
        return rows


async def insert_achievement(user_id: int, achievement: str) -> None:
    """Асинхронно вставляет новое достижение."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
        INSERT OR IGNORE INTO achievements (user_id, achievement)
        VALUES (?, ?)
        ''', (user_id, achievement))
        await db.commit()


async def get_achievements(user_id: int) -> List[str]:
    """Асинхронно получает достижения пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
        SELECT achievement FROM achievements
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
