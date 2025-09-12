from telegram.error import InvalidToken
from datetime import datetime
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, \
    MessageHandler, filters
from db import insert_sleep_data, get_sleep_data, insert_achievement, get_achievements
from utils import load_tips, load_exercises, is_valid_time, calculate_sleep_duration, choose_random_non_repeating, get_token_from_dotenv_file

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


sleep_tips = load_tips()
sleep_exercises = load_exercises()

# Состояния для ConversationHandler
LOGGING_SLEEP, LOGGING_WAKE = range(2)

# Словарь для хранения последнего отправленного упражнения
last_exercise = {}

# Словарь для хранения последнего отправленного совета
last_tip = {}

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

    # Ночной сова: последние 5 записей с поздним отходом (>= 00:30)
    def is_late_bedtime(hhmm: str) -> bool:
        t = datetime.strptime(hhmm, '%H:%M')
        return t.hour > 0 or (t.hour == 0 and t.minute >= 30)

    if len(user_data) >= 5 and all(is_late_bedtime(entry[0]) for entry in user_data[-5:]) and 'Ночной сова' not in achievements:
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
    tip = choose_random_non_repeating(last_tip, user_id, sleep_tips)
    if tip is None:
        await update.message.reply_text('Нет доступных советов сейчас. Добавьте записи в sleep_tips.txt.')
        return
    await update.message.reply_text(f'Совет по улучшению сна: {tip}')

async def send_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    exercise = choose_random_non_repeating(last_exercise, user_id, sleep_exercises)
    if exercise is None:
        await update.message.reply_text('Нет доступных упражнений сейчас. Добавьте записи в sleep_exercises.txt.')
        return
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
    plt.close()

    await update.message.reply_text(f'Средняя продолжительность сна за последнюю неделю: {avg_duration:.2f} часов.')
    with open('weekly_report.png', 'rb') as f:
        await update.message.reply_photo(photo=f)

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
    plt.close()

    await update.message.reply_text(f'Средняя продолжительность сна за последний месяц: {avg_duration:.2f} часов.')
    with open('monthly_report.png', 'rb') as f:
        await update.message.reply_photo(photo=f)

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    achievements = get_achievements(user_id)

    if not achievements:
        await update.message.reply_text('У вас пока нет достижений.')
    else:
        await update.message.reply_text(f'Ваши достижения: {", ".join(achievements)}')

def main() -> None:
    try:
        token = get_token_from_dotenv_file()
        application = Application.builder().token(token).build()

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
    except InvalidToken:
        print('ОШИБКА: Неверный токен Telegram-бота. Пожалуйста, проверьте ваш .env файл.')
    except Exception as e:
        print(f'Произошла непредвиденная ошибка: {e}')

if __name__ == '__main__':
    main()