from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from db import insert_sleep_data, get_sleep_data
from utils import is_valid_time
import achievements

# Состояния для ConversationHandler
LOGGING_SLEEP, LOGGING_WAKE = range(2)


async def has_sleep_data_for_today(user_id):
    today = datetime.now().date().isoformat()
    sleep_data = await get_sleep_data(user_id)
    return any(entry[2] == today for entry in sleep_data)


async def log_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id

    # Проверка, вводил ли пользователь данные о сне сегодня
    if await has_sleep_data_for_today(user_id):
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

    await insert_sleep_data(user_id, sleep_time, wake_time, datetime.now().date().isoformat())

    new_achievements = await achievements.check_achievements(user_id)
    if new_achievements:
        await update.message.reply_text(f'Поздравляем! Вы получили новое достижение: {", ".join(new_achievements)}')

    await update.message.reply_text(f'Данные о сне сохранены:\nЛегли спать в {sleep_time}, проснулись в {wake_time}.')
    return ConversationHandler.END
