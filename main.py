from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, InlineQueryHandler
from telegram.error import InvalidToken

import logging
from utils import get_token_from_dotenv_file
from handlers import load_data
import handlers
import reports
from db import create_tables


def main() -> None:
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    """Основная функция для запуска бота."""
    try:
        token = get_token_from_dotenv_file()

        # Создание application и передача post_init для асинхронной инициализации
        application = Application.builder().token(token).post_init(
            create_tables).post_init(load_data).build()

        # Регистрация обработчиков
        application.add_handler(CommandHandler('start', handlers.start))
        application.add_handler(MessageHandler(filters.Regex(
            '^Старт$'), handlers.show_wake_time_keyboard))
        application.add_handler(CommandHandler('tips', handlers.send_tips))
        application.add_handler(MessageHandler(
            filters.Regex('^Советы$'), handlers.send_tips))
        application.add_handler(CommandHandler(
            'exercises', handlers.send_exercises))
        application.add_handler(MessageHandler(
            filters.Regex('^Упражнения$'), handlers.send_exercises))
        application.add_handler(MessageHandler(filters.Regex(
            '^Графики сна$'), handlers.show_reports_menu))
        application.add_handler(CommandHandler(
            'weekly_report', reports.send_weekly_report))
        application.add_handler(MessageHandler(
            filters.Regex('^За неделю$'), reports.send_weekly_report))
        application.add_handler(CommandHandler(
            'monthly_report', reports.send_monthly_report))
        application.add_handler(MessageHandler(
            filters.Regex('^За месяц$'), reports.send_monthly_report))
        application.add_handler(MessageHandler(
            filters.Regex('^Назад$'), handlers.start))
        application.add_handler(CommandHandler(
            'help', handlers.send_help_message))
        application.add_handler(CommandHandler(
            'achievements', handlers.show_achievements))
        application.add_handler(MessageHandler(
            filters.Regex('^Достижения$'), handlers.show_achievements))

        # Добавление ConversationHandler для логирования сна
        application.add_handler(handlers.get_log_sleep_conv_handler())

        # Обработчик для inline-кнопок
        application.add_handler(CallbackQueryHandler(handlers.show_times))
        application.add_handler(InlineQueryHandler(handlers.share_achievement))

        # Запуск бота
        application.run_polling()
    except InvalidToken:
        logger.error('ОШИБКА: Неверный токен Telegram-бота. Пожалуйста, проверьте ваш .env файл.')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка: {e}', exc_info=True)


if __name__ == '__main__':
    main()
