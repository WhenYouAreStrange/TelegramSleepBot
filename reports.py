import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from utils import calculate_sleep_duration, load_sleep_data

sleep_data = load_sleep_data()

async def send_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_data = sleep_data.get(user_id, [])
    if len(user_data) == 0:
        await update.message.reply_text('Нет данных о сне за последнюю неделю.')
        return
    last_week_data = user_data[-7:]
    durations = [calculate_sleep_duration(entry['sleep_time'], entry['wake_time']) for entry in last_week_data]
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
    user_data = sleep_data.get(user_id, [])
    if len(user_data) == 0:
        await update.message.reply_text('Нет данных о сне за последний месяц.')
        return
    last_month_data = user_data[-30:]
    durations = [calculate_sleep_duration(entry['sleep_time'], entry['wake_time']) for entry in last_month_data]
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