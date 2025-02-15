import numpy as np
from pybit.unified_trading import HTTP
from cfg import symb, bykey, bysecret, tgID, tgtoken
from logs.logging_config import logging
from telebot import TeleBot
from features.market import get_last_5_weeks_and_low_price, get_price_or_change, get_buy_sell_ratio
from datetime import datetime, timedelta

# Создаем глобальный объект сессии (создание сессии API для работы с Bybit)
session = HTTP(testnet=False, api_key=bykey, api_secret=bysecret)
bot = TeleBot(tgtoken)

# Хранение времени последнего уведомления для каждого пользователя
last_notification_time = {}

def calculate_rsi(timeframe):
    try:
        logging.info(f"Расчет RSI для таймфрейма: {timeframe}")
        close = session.get_kline(category="spot", symbol=symb, interval=timeframe, limit=100).get('result', {}).get('list', [])
        if not close:
            logging.warning("Нет данных для расчета RSI")
            return "Нет данных"
        
        close_prices = np.array([i[4] for i in reversed(close)], dtype='float')
        deltas = np.diff(close_prices)
        seed = deltas[:15]
        up = seed[seed >= 0].sum() / 14
        down = -seed[seed < 0].sum() / 14
        rs = up / down
        rsi = np.zeros_like(close_prices)
        rsi[:14] = 100. - 100. / (1. + rs)
        
        for i in range(14, len(close_prices)):
            delta = deltas[i-1]
            upval = delta if delta > 0 else 0
            downval = -delta if delta < 0 else 0
            up = (up * 13 + upval) / 14
            down = (down * 13 + downval) / 14
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        rsi_value = round(rsi[-1], 2)
        logging.info(f"RSI рассчитан: {rsi_value}")
        return rsi_value
    except Exception as e:
        logging.error(f"Ошибка при расчете RSI: {e}")
        return "Ошибка"

def check_rsi_and_notify():
    logging.info("Проверка RSI и отправка уведомлений")
    rsi = calculate_rsi("1")
    if isinstance(rsi, str):
        return  # Если произошла ошибка при расчете RSI, ничего не делаем

    current_time = datetime.now()
    for user_id in tgID:
        try:
            if user_id in last_notification_time:
                elapsed_time = current_time - last_notification_time[user_id]
                if elapsed_time < timedelta(minutes=15):
                    continue  # Пропускаем уведомление, если прошло меньше 15 минут

            if rsi < 30:
                send_rsi_notification(user_id, rsi, "RSI меньше 30")
            elif rsi < 35:
                send_rsi_notification(user_id, rsi, "RSI меньше 35")
            elif rsi > 70:
                send_rsi_notification(user_id, rsi, "RSI больше 70")

            last_notification_time[user_id] = current_time  # Обновляем время последнего уведомления
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления для user_id {user_id}: {e}")

def send_rsi_notification(user_id, rsi, title):
    try:
        screenshot, lowprice14d = get_last_5_weeks_and_low_price()
        current_price = get_price_or_change('price')
        
        if lowprice14d is None or current_price is None:
            raise ValueError("Не удалось получить необходимые данные.")
        
        change_percent = round((float(current_price) - lowprice14d) / lowprice14d * 100, 2)
        buy_sell_ratio = get_buy_sell_ratio("1")
        
        caption = (
            f"{title}\n"
            f"📉 Изменение за 14 дней: {change_percent}%\n"
            f"📊 RSI: {rsi}\n"
            f"📈 {buy_sell_ratio}\n"
            f"💲 Текущая цена BTC: {current_price} USDT"
        )
        
        bot.send_photo(chat_id=user_id, photo=screenshot, caption=caption)
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления для user_id {user_id}: {e}")
        bot.send_message(user_id, f"⚠️ Ошибка при отправке уведомления: {e}")
