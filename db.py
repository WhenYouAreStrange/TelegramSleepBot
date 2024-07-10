import sqlite3

def create_tables():
    conn = sqlite3.connect('sleepbot.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sleep_data (
        user_id INTEGER,
        sleep_time TEXT,
        wake_time TEXT,
        date TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        user_id INTEGER,
        achievement TEXT
    )
    ''')
    conn.commit()
    conn.close()

create_tables()