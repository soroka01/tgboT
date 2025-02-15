import schedule
from database import init_db
from tasks.scheduler import start_scheduler
from handlers import register_handlers
from tasks.runner import daily_update, check_price_alerts, check_rsi_and_notify
from bot_instance import bot, session

# Инициализация базы данных
init_db()

# Регистрация обработчиков
register_handlers(bot, session)

# Планирование задач
schedule.every().minute.do(daily_update)
schedule.every().minute.do(check_price_alerts)
schedule.every().minute.do(check_rsi_and_notify)

# Запуск планировщика в отдельном потоке
start_scheduler()

if __name__ == '__main__':
    bot.polling(none_stop=True)  # Запуск бота в режиме постоянного опроса
