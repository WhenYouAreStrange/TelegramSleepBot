import random
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, \
    MessageHandler, filters
import sqlite3

# Токен, который ты получил от BotFather
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Данные о времени
sleep_schedule = {
    '6:00': ['20:45', '22:15'],
    '6:30': ['21:15', '22:45'],
    '7:00': ['21:45', '23:15'],
    '7:30': ['22:15', '23:45'],
    '8:00': ['22:45', '00:15'],
    '8:30': ['23:15', '00:45'],
    '9:00': ['23:45', '01:15'],
    '9:30': ['00:15', '01:45']
}

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

# Функция для чтения советов и упражнений из текстовых файлов
def load_tips(filename='sleep_tips.txt'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            tips = file.readlines()
        return [tip.strip() for tip in tips]
    except FileNotFoundError:
        return []

def load_exercises(filename='sleep_exercises.txt'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            exercises = file.readlines()
        return [exercise.strip() for exercise in exercises]
    except FileNotFoundError:
        return []

sleep_tips = load_tips()
sleep_exercises = load_exercises()

# Состояния для ConversationHandler
LOGGING_SLEEP, LOGGING_WAKE = range(2)

# Словарь для хранения последнего отправленного упражнения
last_exercise = {}

# Словарь для хранения последнего отправленного совета
last_tip = {}

# Функция для проверки корректности времени
def is_valid_time(time_str):
    match = re.match(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$', time_str)
    return bool(match)

# Функции для работы с SQLite
def insert_sleep_data(user_id, sleep_time, wake_time, date):
    conn = sqlite3.connect('sleepbot.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO sleep_data (user_id, sleep_time, wake_time, date)
    VALUES (?, ?, ?, ?)
    ''', (user_id, sleep_time, wake_time, date))
    conn.commit()
    conn.close()

def get_sleep_data(user_id):
    conn = sqlite3.connect('sleepbot.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT sleep_time, wake_time, date FROM sleep_data
    WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_achievement(user_id, achievement):
    conn = sqlite3.connect('sleepbot.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO achievements (user_id, achievement)
    VALUES (?, ?)
    ''', (user_id, achievement))
    conn.commit()
    conn.close()

def get_achievements(user_id):
    conn = sqlite3.connect('sleepbot.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT achievement FROM achievements
    WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def check_achievements(user_id):
    user_data = get_sleep_data(user_id)
    achievements = get_achievements(user_id)

    new_achievements = []

    if len(user_data) >= 3 and 'Начинающий сонник' not in achievements:
        new_achievements.append('Начинающий сонник')

    if len(user_data) >= 7 and 'Продвинутый сонник' not in achievements:
        new_achievements.append('Продвинутый сонник')

    if len(user_data) >= 30 and 'Мастер сна' not in achievements:
        new_achievements.append('Мастер сна')

    if all(datetime.strptime(entry[0], '%H:%M').hour < 22 for entry in user_data[-5:]) and 'Ранний пташка' not in achievements:
        new_achievements.append('Ранний пташка')

    if all(datetime.strptime(entry[0], '%H:%M').hour >= 0 for entry in user_data[-5:]) and 'Ночной сова' not in achievements:
        new_achievements.append('Ночной сова')

    for achievement in new_achievements:
        insert_achievement(user_id, achievement)

    return new_achievements

# Функция для проверки наличия данных за текущий день
def has_sleep_data_for_today(user_id):
    today = datetime.now().date().isoformat()
    sleep_data = get_sleep_data(user_id)
    return any(entry[2] == today for entry in sleep_data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton(time, callback_data=time)] for time in sleep_schedule.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Выберите время, когда нужно проснуться:', reply_markup=reply_markup)

async def show_times(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    wake_time = query.data
    sleep_times = sleep_schedule[wake_time]

    response_text = f'Если нужно проснуться в {wake_time}, то лучше лечь спать в одно из следующих времён: {", ".join(sleep_times)}'
    await query.edit_message_text(text=response_text)

async def send_tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    tip = random.choice(sleep_tips)

    # Проверка, чтобы не отправлять подряд два одинаковых совета
    while user_id in last_tip and tip == last_tip[user_id]:
        tip = random.choice(sleep_tips)

    last_tip[user_id] = tip
    await update.message.reply_text(f'Совет по улучшению сна: {tip}')

async def send_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    exercise = random.choice(sleep_exercises)

    # Проверка, чтобы не отправлять подряд два одинаковых упражнения
    while user_id in last_exercise and exercise == last_exercise[user_id]:
        exercise = random.choice(sleep_exercises)

    last_exercise[user_id] = exercise
    await update.message.reply_text(f'Упражнение для улучшения сна: {exercise}')

async def log_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id

    # Проверка, вводил ли пользователь данные о сне сегодня
    if has_sleep_data_for_today(user_id):
        await update.message.reply_text('Вы уже вводили данные о сне сегодня. Пожалуйста, попробуйте снова завтра.')
        return ConversationHandler.END

    await update.message.reply_text('Пожалуйста, введите время, когда вы легли спать (в формате ЧЧ:ММ):')
    return LOGGING_SLEEP

async def log_wake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    sleep_time = update.message.text

    if not is_valid_time(sleep_time):
        await update.message.reply_text(
            'Некорректное время. Пожалуйста, введите время в формате ЧЧ:ММ (например, 22:30).')
        return LOGGING_SLEEP

    context.user_data['sleep_time'] = sleep_time
    await update.message.reply_text('Пожалуйста, введите время, когда вы проснулись (в формате ЧЧ:ММ):')
    return LOGGING_WAKE

async def save_sleep_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    wake_time = update.message.text

    if not is_valid_time(wake_time):
        await update.message.reply_text(
            'Некорректное время. Пожалуйста, введите время в формате ЧЧ:ММ (например, 06:30).')
        return LOGGING_WAKE

    sleep_time = context.user_data.get('sleep_time')
    if not sleep_time:
        await update.message.reply_text('Ошибка: не найдено время, когда вы легли спать.')
        return ConversationHandler.END

    insert_sleep_data(user_id, sleep_time, wake_time, datetime.now().date().isoformat())

    new_achievements = check_achievements(user_id)
    if new_achievements:
        await update.message.reply_text(f'Поздравляем! Вы получили новое достижение: {", ".join(new_achievements)}')

    await update.message.reply_text(f'Данные о сне сохранены: Легли спать в {sleep_time}, проснулись в {wake_time}.')
    return ConversationHandler.END

def calculate_sleep_duration(sleep_time: str, wake_time: str) -> float:
    sleep_dt = datetime.strptime(sleep_time, '%H:%M')
    wake_dt = datetime.strptime(wake_time, '%H:%M')
    if wake_dt < sleep_dt:
        wake_dt += timedelta(days=1)
    duration = (wake_dt - sleep_dt).seconds / 3600
    return duration

async def send_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_data = get_sleep_data(user_id)
    if len(user_data) == 0:
        await update.message.reply_text('Нет данных о сне за последнюю неделю.')
        return

    last_week_data = user_data[-7:]
    durations = [calculate_sleep_duration(entry[0], entry[1]) for entry in last_week_data]
    avg_duration = sum(durations) / len(durations)

    plt.figure(figsize=(10, 5))
    plt.plot(durations, marker='o')
    plt.title('Продолжительность сна за последнюю неделю')
    plt.xlabel('Дни')
    plt.ylabel('Часы сна')
    plt.grid(True)
    plt.savefig('weekly_report.png')

    await update.message.reply_text(f'Средняя продолжительность сна за последнюю неделю: {avg_duration:.2f} часов.')
    await update.message.reply_photo(photo=open('weekly_report.png', 'rb'))

async def send_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_data = get_sleep_data(user_id)
    if len(user_data) == 0:
        await update.message.reply_text('Нет данных о сне за последний месяц.')
        return

    last_month_data = user_data[-30:]
    durations = [calculate_sleep_duration(entry[0], entry[1]) for entry in last_month_data]
    avg_duration = sum(durations) / len(durations)

    plt.figure(figsize=(10, 5))
    plt.plot(durations, marker='o')
    plt.title('Продолжительность сна за последний месяц')
    plt.xlabel('Дни')
    plt.ylabel('Часы сна')
    plt.grid(True)
    plt.savefig('monthly_report.png')

    await update.message.reply_text(f'Средняя продолжительность сна за последний месяц: {avg_duration:.2f} часов.')
    await update.message.reply_photo(photo=open('monthly_report.png', 'rb'))

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    achievements = get_achievements(user_id)

    if not achievements:
        await update.message.reply_text('У вас пока нет достижений.')
    else:
        await update.message.reply_text(f'Ваши достижения: {", ".join(achievements)}')

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('tips', send_tips))
    application.add_handler(CommandHandler('exercises', send_exercises))
    application.add_handler(CommandHandler('weekly_report', send_weekly_report))
    application.add_handler(CommandHandler('monthly_report', send_monthly_report))
    application.add_handler(CommandHandler('achievements', show_achievements))

    # Обработчик для записи данных о сне
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('log_sleep', log_sleep)],
        states={
            LOGGING_SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_wake)],
            LOGGING_WAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_sleep_data)],
        },
        fallbacks=[CommandHandler('log_sleep', log_sleep)],  # Добавляем обработчик для fallbacks
    )
    application.add_handler(conv_handler)

    # Обработчик для выбора времени пробуждения
    application.add_handler(CallbackQueryHandler(show_times))

    application.run_polling()

if __name__ == '__main__':
    main()