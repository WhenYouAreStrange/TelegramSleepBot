from telegram.error import InvalidToken
from datetime import datetime
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, \
    MessageHandler, filters
from db import insert_sleep_data, get_sleep_data, insert_achievement, get_achievements
from utils import load_tips, load_exercises, is_valid_time, calculate_sleep_duration, choose_random_non_repeating, get_token_from_dotenv_file
from keyboards import get_main_keyboard, get_wake_time_keyboard, get_reports_keyboard

import achievements
import reports
import log_sleep

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


# Словарь для хранения последнего отправленного упражнения
last_exercise = {}

# Словарь для хранения последнего отправленного совета
last_tip = {}



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Бот запущен. Используйте клавиатуру для взаимодействия.',
        reply_markup=get_main_keyboard()
    )

async def show_wake_time_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет inline-клавиатуру для выбора времени пробуждения."""
    await update.message.reply_text(
        'Выберите время, когда нужно проснуться:',
        reply_markup=get_wake_time_keyboard(sleep_schedule)
    )

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



async def send_help_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение."""
    with open('help.txt', 'r', encoding='utf-8') as f:
        help_text = f.read()
    await update.message.reply_text(help_text)

async def show_reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню выбора отчетов."""
    await update.message.reply_text(
        'Выберите период для отчета:',
        reply_markup=get_reports_keyboard()
    )

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_achievements = get_achievements(user_id)

    if not user_achievements:
        await update.message.reply_text('У вас пока нет достижений.')
    else:
        await update.message.reply_text(f'Ваши достижения: {", ".join(user_achievements)}')

def main() -> None:
    try:
        token = get_token_from_dotenv_file()
        application = Application.builder().token(token).build()

        # Обработчики команд
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.Regex('^Старт$'), show_wake_time_keyboard))
        application.add_handler(CommandHandler('tips', send_tips))
        application.add_handler(MessageHandler(filters.Regex('^Советы$'), send_tips))
        application.add_handler(CommandHandler('exercises', send_exercises))
        application.add_handler(MessageHandler(filters.Regex('^Упражнения$'), send_exercises))
        application.add_handler(MessageHandler(filters.Regex('^Графики сна$'), show_reports_menu))
        application.add_handler(CommandHandler('weekly_report', reports.send_weekly_report))
        application.add_handler(MessageHandler(filters.Regex('^За неделю$'), reports.send_weekly_report))
        application.add_handler(CommandHandler('monthly_report', reports.send_monthly_report))
        application.add_handler(MessageHandler(filters.Regex('^За месяц$'), reports.send_monthly_report))
        application.add_handler(MessageHandler(filters.Regex('^Назад$'), start))
        application.add_handler(CommandHandler('help', send_help_message))
        application.add_handler(CommandHandler('achievements', show_achievements))
        application.add_handler(MessageHandler(filters.Regex('^Достижения$'), show_achievements))

        # Обработчик для записи данных о сне
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('log_sleep', log_sleep.log_sleep),
                MessageHandler(filters.Regex('^Записать сон$'), log_sleep.log_sleep)
            ],
            states={
                log_sleep.LOGGING_SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_sleep.log_wake)],
                log_sleep.LOGGING_WAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_sleep.save_sleep_data)],
            },
            fallbacks=[CommandHandler('log_sleep', log_sleep.log_sleep)],  # Добавляем обработчик для fallbacks
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