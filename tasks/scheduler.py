import time
from threading import Thread
import schedule
from logs.logging_config import logging

# Функция для запуска планировщика
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Запуск планировщика в отдельном потоке
def start_scheduler():
    Thread(target=run_schedule).start()