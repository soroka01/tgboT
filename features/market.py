from pybit.unified_trading import HTTP
from cfg import symb, bykey, bysecret
import matplotlib.pyplot as plt
import io
import requests
import numpy as np
from logs.logging_config import logging
from datetime import datetime, timedelta
from cfg import tgID, tgtoken
from bot_instance import bot
from database import load_user_rsi_alerts

# Создание сессии для работы с Bybit API
session = HTTP(testnet=False, api_key=bykey, api_secret=bysecret)

# Функция для получения данных о цене
def get_price_data(interval="D"):
    logging.info(f"Получение данных о цене за интервал: {interval}")
    try:
        kline = session.get_kline(category="spot", symbol=symb, interval=interval, limit=1).get('result', {}).get('list', [])
        if not kline:
            logging.warning("Данные о цене не найдены")
            return None, None
        open_price, close_price = kline[0][1], kline[0][4]
        return float(open_price), float(close_price)
    except Exception as e:
        logging.error(f"Ошибка при получении данных о цене: {e}")
        return None, None

# Функция для получения текущей цены или дневного изменения
def get_price_or_change(PriceOrDailyChange):
    logging.info(f"Получение цены или дневного изменения: {PriceOrDailyChange}")
    open_price, close_price = get_price_data()
    if open_price is None or close_price is None:
        logging.warning("Данные о цене недоступны")
        return "Данные недоступны"
    if PriceOrDailyChange == 'price':
        return close_price
    if PriceOrDailyChange == 'change':
        return f"{round(((close_price - open_price) / close_price) * 100, 2)}%"

# Функция для вычисления RSI
def calculate_rsi(timeframe):
    logging.info(f"Вычисление RSI за таймфрейм: {timeframe}")
    try:
        klines = session.get_kline(category="spot", symbol=symb, interval=timeframe, limit=100).get('result', {}).get('list', [])
        close_prices = [float(kline[4]) for kline in klines]
        close_prices = np.array(list(reversed(close_prices)), dtype='float')
        
        n = 14
        deltas = np.diff(close_prices)
        seed = deltas[:n+1]
        up = seed[seed >= 0].sum() / n
        down = -seed[seed < 0].sum() / n
        rs = up / down
        rsi = np.zeros_like(close_prices)
        rsi[:n] = 100. - 100. / (1. + rs)
        
        for i in range(n, len(close_prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (n - 1) + upval) / n
            down = (down * (n - 1) + downval) / n
            
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        return round(rsi[-1], 2)
    except Exception as e:
        logging.error(f"Ошибка при вычислении RSI: {e}")
        return "Ошибка при вычислении RSI"

# Функция для получения соотношения покупок и продаж
def get_buy_sell_ratio(timeframe):
    logging.info(f"Получение соотношения покупок и продаж за таймфрейм: {timeframe}")
    periods = {60: "1h", "D": "1d"}
    url = f"https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period={periods.get(timeframe, '1h')}&limit=1"
    try:
        response = requests.get(url).json()
        data = response.get('result', {}).get('list', [{}])[0]
        buy, sell = data.get('buyRatio', "N/A"), data.get('sellRatio', "N/A")
        return f"🟢 {buy}  {sell} 🔴"
    except Exception as e:
        logging.error(f"Ошибка при получении соотношения покупок и продаж: {e}")
        return f"Ошибка: {e}"

# Функция для получения данных за последние 5 недель и минимальной цены за 14 дней
def get_last_5_weeks_and_low_price():
    logging.info("Получение данных за последние 5 недель и минимальной цены за 14 дней")
    try:
        lim = 7 * 5  # 5 недель
        klines = session.get_kline(category="spot", symbol=symb, interval='D', limit=lim).get('result', {}).get('list', [])
        logging.info(f"Данные свечей: {klines}")
        if not klines:
            logging.warning("Данные свечей не найдены")
            return None, None
        
        plt.figure()
        width = 0.4
        width2 = 0.05
        col1 = 'green'
        col2 = 'red'
        
        prices = sorted(klines[:14], key=lambda x: float(x[3]))
        lowprice14d = float(prices[0][3])
        
        for i in klines:
            open_price, high_price, low_price, close_price = map(float, i[1:5])
            color = col1 if close_price > open_price else col2
            plt.bar(i[0], close_price - open_price, width, bottom=open_price, color=color)
            plt.bar(i[0], high_price - close_price, width2, bottom=close_price, color=color)
            plt.bar(i[0], low_price - open_price, width2, bottom=open_price, color=color)
        
        plt.axhline(y=lowprice14d, color='purple', linestyle='solid')
        plt.xticks([])
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.clf()
        plt.close()
        
        return buf, lowprice14d
    except Exception as e:
        logging.error(f"Ошибка при получении данных за последние 5 недель и минимальной цены: {e}")
        return None, None

# Хранение времени последнего уведомления для каждого пользователя
last_notification_time = {}

def check_rsi_and_notify():
    logging.info("Проверка RSI и отправка уведомлений")
    rsi = calculate_rsi("1")
    if isinstance(rsi, str):
        return  # Если произошла ошибка при расчете RSI, ничего не делаем
    
    current_time = datetime.now()
    for user_id in tgID:
        try:
            alerts = load_user_rsi_alerts(user_id)
            for alert in alerts:
                if alert['condition'] == 'below' and rsi < alert['level']:
                    send_rsi_notification(user_id, rsi, f"RSI меньше {alert['level']}")
                elif alert['condition'] == 'above' and rsi > alert['level']:
                    send_rsi_notification(user_id, rsi, f"RSI больше {alert['level']}")
            
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
