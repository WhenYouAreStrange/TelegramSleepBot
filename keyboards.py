from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard():
    """Возвращает основную клавиатуру с кнопками."""
    reply_keyboard = [
        [KeyboardButton("Старт")],
        [KeyboardButton("Советы"), KeyboardButton("Упражнения")],
        [KeyboardButton("Записать сон"), KeyboardButton("Достижения")],
        [KeyboardButton("Графики сна")]
    ]
    return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)


def get_wake_time_keyboard(sleep_schedule):
    """Возвращает inline-клавиатуру для выбора времени пробуждения."""
    inline_keyboard = [[InlineKeyboardButton(
        time, callback_data=time)] for time in sleep_schedule.keys()]
    return InlineKeyboardMarkup(inline_keyboard)


def get_reports_keyboard():
    """Возвращает клавиатуру для выбора отчета."""
    reply_keyboard = [
        [KeyboardButton("За неделю"), KeyboardButton("За месяц")],
        [KeyboardButton("Назад")]
    ]
    return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
