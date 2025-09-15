import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ContextTypes
from db import get_sleep_data
from utils import calculate_sleep_duration

async def send_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_data = get_sleep_data(user_id)
    if len(user_data) < 7:
        await update.message.reply_text('Недостаточно данных для формирования недельного отчета.')
        return

    last_week_data = user_data[-7:]
    durations = [calculate_sleep_duration(entry[0], entry[1]) for entry in last_week_data]
    avg_duration = sum(durations) / len(durations)

    plt.figure(figsize=(10, 5))
    plt.plot(range(1, 8), durations, marker='o')
    plt.title('Продолжительность сна за последнюю неделю')
    plt.xlabel('Дни')
    plt.ylabel('Часы сна')
    plt.grid(True)
    plt.xticks(range(1, 8))
    plt.savefig(f'weekly_report_{user_id}.png')
    plt.close()

    await update.message.reply_text(f'Средняя продолжительность сна за последнюю неделю: {avg_duration:.2f} часов.')
    with open(f'weekly_report_{user_id}.png', 'rb') as f:
        await update.message.reply_photo(photo=f)

async def send_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_data = get_sleep_data(user_id)
    if len(user_data) < 30:
        await update.message.reply_text('Недостаточно данных для формирования месячного отчета.')
        return

    last_month_data = user_data[-30:]
    durations = [calculate_sleep_duration(entry[0], entry[1]) for entry in last_month_data]
    avg_duration = sum(durations) / len(durations)

    plt.figure(figsize=(10, 5))
    plt.plot(range(1, 31), durations, marker='o')
    plt.title('Продолжительность сна за последний месяц')
    plt.xlabel('Дни')
    plt.ylabel('Часы сна')
    plt.grid(True)
    plt.xticks(range(1, 31, 2))
    plt.savefig(f'monthly_report_{user_id}.png')
    plt.close()

    await update.message.reply_text(f'Средняя продолжительность сна за последний месяц: {avg_duration:.2f} часов.')
    with open(f'monthly_report_{user_id}.png', 'rb') as f:
        await update.message.reply_photo(photo=f)