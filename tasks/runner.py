import logging
import schedule
import time
from functions import daily_update, check_price_alerts, get_rsi_and_send_message, get_moscow_time
from analysis import calculate_rsi, get_last_5_weeks_and_low_price, get_buy_sell_ratio, get_price_or_change, send_rsi_notification, check_rsi_and_notify
from logs.logging_config import logging
from cfg import tgID

# Планирование задач
schedule.every().second.do(get_moscow_time)
schedule.every().minute.do(daily_update)
schedule.every().minute.do(check_price_alerts)
schedule.every().minute.do(check_rsi_and_notify)

# Функция для запуска планировщика
def run_schedule():
    logging.info("Запуск планировщика")
    while True:
        schedule.run_pending()
        time.sleep(1)

def daily_update():
    logging.info("Запуск ежедневного обновления")
    moscow_time = get_moscow_time()
    if moscow_time.hour == 8 and moscow_time.minute == 30:
        for user_id in tgID:
            get_rsi_and_send_message(user_id)