from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.error import InvalidToken

from utils import get_token_from_dotenv_file
import handlers
import reports
from db import create_tables


def main() -> None:
    """Основная функция для запуска бота."""
    try:
        token = get_token_from_dotenv_file()
        
        # Создание application и передача post_init для асинхронной инициализации
        application = Application.builder().token(token).post_init(create_tables).build()

        # Регистрация обработчиков
        application.add_handler(CommandHandler('start', handlers.start))
        application.add_handler(MessageHandler(filters.Regex('^Старт$'), handlers.show_wake_time_keyboard))
        application.add_handler(CommandHandler('tips', handlers.send_tips))
        application.add_handler(MessageHandler(filters.Regex('^Советы$'), handlers.send_tips))
        application.add_handler(CommandHandler('exercises', handlers.send_exercises))
        application.add_handler(MessageHandler(filters.Regex('^Упражнения$'), handlers.send_exercises))
        application.add_handler(MessageHandler(filters.Regex('^Графики сна$'), handlers.show_reports_menu))
        application.add_handler(CommandHandler('weekly_report', reports.send_weekly_report))
        application.add_handler(MessageHandler(filters.Regex('^За неделю$'), reports.send_weekly_report))
        application.add_handler(CommandHandler('monthly_report', reports.send_monthly_report))
        application.add_handler(MessageHandler(filters.Regex('^За месяц$'), reports.send_monthly_report))
        application.add_handler(MessageHandler(filters.Regex('^Назад$'), handlers.start))
        application.add_handler(CommandHandler('help', handlers.send_help_message))
        application.add_handler(CommandHandler('achievements', handlers.show_achievements))
        application.add_handler(MessageHandler(filters.Regex('^Достижения$'), handlers.show_achievements))

        # Добавление ConversationHandler для логирования сна
        application.add_handler(handlers.get_log_sleep_conv_handler())

        # Обработчик для inline-кнопок
        application.add_handler(CallbackQueryHandler(handlers.show_times))

        # Запуск бота
        application.run_polling()
    except InvalidToken:
        print('ОШИБКА: Неверный токен Telegram-бота. Пожалуйста, проверьте ваш .env файл.')
    except Exception as e:
        print(f'Произошла непредвиденная ошибка: {e}')

if __name__ == '__main__':
    main()