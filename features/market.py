from pybit.unified_trading import HTTP
from cfg import symb, bykey, bysecret
import matplotlib.pyplot as plt
import io
import requests
from logs.logging_config import logging

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
