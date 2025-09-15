from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from db import get_achievements
from utils import load_tips, load_exercises, choose_random_non_repeating
from keyboards import get_main_keyboard, get_wake_time_keyboard, get_reports_keyboard
import reports
import log_sleep
from config import SLEEP_SCHEDULE

sleep_tips = load_tips()
sleep_exercises = load_exercises()

# Словари для хранения последних отправленных элементов
last_exercise = {}
last_tip = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и основную клавиатуру."""
    await update.message.reply_text(
        'Бот запущен. Используйте клавиатуру для взаимодействия.',
        reply_markup=get_main_keyboard()
    )

async def show_wake_time_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет inline-клавиатуру для выбора времени пробуждения."""
    await update.message.reply_text(
        'Выберите время, когда нужно проснуться:',
        reply_markup=get_wake_time_keyboard(SLEEP_SCHEDULE)
    )

async def show_times(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор времени пробуждения и показывает рекомендуемое время сна."""
    query = update.callback_query
    await query.answer()

    wake_time = query.data
    sleep_times = SLEEP_SCHEDULE.get(wake_time, [])

    response_text = f'Если нужно проснуться в {wake_time}, то лучше лечь спать в одно из следующих времён: {", ".join(sleep_times)}'
    await query.edit_message_text(text=response_text)

async def send_tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет случайный совет по сну."""
    user_id = update.message.from_user.id
    tip = choose_random_non_repeating(last_tip, user_id, sleep_tips)
    if tip is None:
        await update.message.reply_text('Нет доступных советов сейчас. Добавьте записи в sleep_tips.txt.')
        return
    await update.message.reply_text(f'Совет по улучшению сна: {tip}')

async def send_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет случайное упражнение для расслабления."""
    user_id = update.message.from_user.id
    exercise = choose_random_non_repeating(last_exercise, user_id, sleep_exercises)
    if exercise is None:
        await update.message.reply_text('Нет доступных упражнений сейчас. Добавьте записи в sleep_exercises.txt.')
        return
    await update.message.reply_text(f'Упражнение для улучшения сна: {exercise}')

async def send_help_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение."""
    try:
        with open('help.txt', 'r', encoding='utf-8') as f:
            help_text = f.read()
        await update.message.reply_text(help_text)
    except FileNotFoundError:
        await update.message.reply_text('Справочная информация не найдена.')

async def show_reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню выбора отчетов."""
    await update.message.reply_text(
        'Выберите период для отчета:',
        reply_markup=get_reports_keyboard()
    )

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает достижения пользователя."""
    user_id = update.message.from_user.id
    user_achievements = await get_achievements(user_id)

    if not user_achievements:
        await update.message.reply_text('У вас пока нет достижений.')
    else:
        await update.message.reply_text(f'Ваши достижения: {", ".join(user_achievements)}')

def get_log_sleep_conv_handler():
    """Возвращает ConversationHandler для логирования сна."""
    return ConversationHandler(
        entry_points=[
            CommandHandler('log_sleep', log_sleep.log_sleep),
            MessageHandler(filters.Regex('^Записать сон$'), log_sleep.log_sleep)
        ],
        states={
            log_sleep.LOGGING_SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_sleep.log_wake)],
            log_sleep.LOGGING_WAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_sleep.save_sleep_data)],
        },
        fallbacks=[CommandHandler('log_sleep', log_sleep.log_sleep)],
    )