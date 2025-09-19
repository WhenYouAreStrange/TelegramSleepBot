from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
import logging
import aiofiles
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from analysis import analyze_sleep_data
from db import get_achievements
from utils import load_tips, load_exercises, choose_random_non_repeating
from keyboards import get_main_keyboard, get_wake_time_keyboard, get_reports_keyboard
import reports
import log_sleep
from config import SLEEP_SCHEDULE
import textwrap

logger = logging.getLogger(__name__)
sleep_tips = []
sleep_exercises = []

# Словари для хранения последних отправленных элементов
last_exercise = {}
last_tip = {}


async def load_data(_):
    """Асинхронно загружает советы и упражнения."""
    global sleep_tips, sleep_exercises
    sleep_tips = await load_tips()
    sleep_exercises = await load_exercises()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и основную клавиатуру."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot.")
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

    response_text = f'Чтобы проснуться в {wake_time}, рекомендуется лечь спать в {" или ".join(sleep_times)}. В этом случае цикл сна завершится удачно, и пробуждение будет легким.'
    await query.edit_message_text(text=response_text)


async def send_tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет персональный или случайный совет по сну."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested a sleep tip.")

    # Попытка получить персональный совет
    personalized_tip = await analyze_sleep_data(user_id)

    if personalized_tip:
        tip = personalized_tip
        final_text = f" - Персональный совет:\n\n{tip}"
    else:
        # Если персональный совет недоступен, отправить случайный
        logger.info(
            f"Not enough data for personalized tip for user {user_id}. Sending random tip.")
        tip = choose_random_non_repeating(last_tip, user_id, sleep_tips)
        if tip is None:
            logger.warning("No random sleep tips available.")
            await update.message.reply_text('Нет доступных советов сейчас. Добавьте записи в sleep_tips.txt.')
            return
        final_text = f" - Совет по улучшению сна\n\n{tip}"

    await update.message.reply_text(final_text)


async def send_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет случайное упражнение для расслабления."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested a sleep exercise.")
    exercise = choose_random_non_repeating(
        last_exercise, user_id, sleep_exercises)
    if exercise is None:
        logger.warning("No sleep exercises available.")
        await update.message.reply_text('Нет доступных упражнений сейчас. Добавьте записи в sleep_exercises.txt.')
        return
    # Формируем итоговый текст
    final_text = f" - Упражнение для улучшения сна\n\n{exercise}"

    await update.message.reply_text(final_text)


async def send_help_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested help.")
    try:
        async with aiofiles.open('help.txt', 'r', encoding='utf-8') as f:
            help_text = await f.read()
        await update.message.reply_text(help_text)
    except FileNotFoundError:
        logger.error("Help file not found.")
        await update.message.reply_text('Справочная информация не найдена.')


async def show_reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню выбора отчетов."""
    await update.message.reply_text(
        'Выберите период для отчета:',
        reply_markup=get_reports_keyboard()
    )


async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает достижения пользователя с кнопками для репоста."""
    user_id = update.message.from_user.id
    user_achievements = await get_achievements(user_id)

    if not user_achievements:
        await update.message.reply_text('У вас пока нет достижений.')
        return

    keyboard = []
    for achievement in user_achievements:
        share_button = InlineKeyboardButton(
            f"Поделиться: {achievement}",
            switch_inline_query=f"Я получил новое достижение '{achievement}' в боте для отслеживания сна!"
        )
        keyboard.append([share_button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Ваши достижения:', reply_markup=reply_markup)


def get_log_sleep_conv_handler():
    """Возвращает ConversationHandler для логирования сна."""
    return ConversationHandler(
        entry_points=[
            CommandHandler('log_sleep', log_sleep.log_sleep),
            MessageHandler(filters.Regex('^Записать сон$'),
                           log_sleep.log_sleep)
        ],
        states={
            log_sleep.LOGGING_SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_sleep.log_wake)],
            log_sleep.LOGGING_WAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_sleep.save_sleep_data)],
        },
        fallbacks=[CommandHandler('log_sleep', log_sleep.log_sleep)],
    )


async def share_achievement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает inline-запросы для репоста достижений."""
    query = update.inline_query.query
    if not query:
        return

    results = [
        InlineQueryResultArticle(
            id=query.upper(),
            title="Поделиться достижением",
            input_message_content=InputTextMessageContent(f"🎉 {query}")
        )
    ]
    await update.inline_query.answer(results)
