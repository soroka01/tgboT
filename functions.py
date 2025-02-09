import io
import time
import pytz
import schedule
import requests
import numpy as np
import matplotlib.pyplot as plt
from telebot import TeleBot
from pybit.unified_trading import HTTP
from datetime import datetime
from cfg import symb, timeframe, tgtoken, tgID, bykey, bysecret

# Создаем глобальный объект сессии (создание сессии API для работы с Bybit и Telegram бота)
session = HTTP(testnet=False, api_key=bykey, api_secret=bysecret)
bot = TeleBot(tgtoken)

#Получает цену закрытия и открытия для заданного интервала времени
def get_price_data(interval="D"):
    kline = session.get_kline(category="spot", symbol=symb, interval=interval, limit=1).get('result', {}).get('list', [])
    if not kline:
        return None, None
    open_price, close_price = kline[0][1], kline[0][4]
    return float(open_price), float(close_price)

#Возвращает текущую цену или дневное изменение в %
def get_price_or_change(PriceOrDailyChange):
    open_price, close_price = get_price_data()
    if close_price is None:
        return "Данные недоступны"
    if PriceOrDailyChange == 'price':
        return close_price
    if PriceOrDailyChange == 'change':
        return f"{round(((close_price - open_price) / close_price) * 100, 2)}%"

#Рассчитывает RSI (индекс относительной силы) для заданного таймфрейма
def calculate_rsi(timeframe):
    close_prices = session.get_kline(category="spot", symbol=symb, interval=timeframe, limit=100).get('result', {}).get('list', [])
    if not close_prices:
        return "Нет данных"
    
    close_prices = np.array([float(i[4]) for i in reversed(close_prices)], dtype='float')
    deltas = np.diff(close_prices)
    n = 14
    seed = deltas[:n+1]
    up = seed[seed >= 0].sum() / n
    down = -seed[seed < 0].sum() / n
    rs = up / down
    rsi = np.zeros_like(close_prices)
    rsi[:n] = 100. - 100. / (1. + rs)
    
    for i in range(n, len(close_prices)):
        delta = deltas[i-1]
        upval = delta if delta > 0 else 0
        downval = -delta if delta < 0 else 0
        up = (up * (n - 1) + upval) / n
        down = (down * (n - 1) + downval) / n
        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)
        
    return round(rsi[-1], 2)

#Получает соотношение покупок и продаж на рынке BTC/USDT
def get_buy_sell_ratio(timeframe):
    periods = {60: "1h", "D": "1d"}
    url = f"https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period={periods.get(timeframe, '1h')}&limit=1"
    
    try:
        response = requests.get(url).json()
        data = response.get('result', {}).get('list', [{}])[0]
        buy, sell = data.get('buyRatio', "N/A"), data.get('sellRatio', "N/A")
        return f"🟢 {buy}  {sell} 🔴"
    except Exception as e:
        return f"Ошибка: {e}"

#Получает график последних 5 недель и минимальную цену за 14 дней
def get_last_5_weeks_and_low_price():
    lim = 7 * 5  # 5 недель
    klines = session.get_kline(category="spot", symbol=symb, interval='D', limit=lim).get('result', {}).get('list', [])
    
    plt.figure()
    width = 0.4
    width2 = 0.05
    col1 = 'green'
    col2 = 'red'
    
    x = 0
    prices = []
    for i in klines:
        x += 1
        prices.append(i)  
        if x == 14:
            break
    prices = sorted(prices, reverse=False)
    klines = sorted(klines, reverse=False)
    
    for i in klines:
        if i[4] > i[1]:
            plt.bar(i[0], float(i[4]) - float(i[1]), width, bottom=float(i[1]), color=col1)
            plt.bar(i[0], float(i[2]) - float(i[4]), width2, bottom=float(i[4]), color=col1)
            plt.bar(i[0], float(i[3]) - float(i[1]), width2, bottom=float(i[1]), color=col1)
        elif i[4] < i[1]:
            plt.bar(i[0], float(i[4]) - float(i[1]), width, bottom=float(i[1]), color=col2)
            plt.bar(i[0], float(i[2]) - float(i[1]), width2, bottom=float(i[1]), color=col2)
            plt.bar(i[0], float(i[3]) - float(i[4]), width2, bottom=float(i[4]), color=col2)
    
    lowprices14d = [float(i[3]) for i in prices]
    lowprice14d = min(lowprices14d)
    
    plt.axhline(y=lowprice14d, color='purple', linestyle='solid')
    plt.xticks([])
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf, lowprice14d

#Получение текущего времени по МСК
def get_moscow_time(pytz):
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow_tz)
    return moscow_time

#Запуск ежедневного обновления в 08:30 по МСК
def daily_update():
    moscow_time = get_moscow_time()
    if moscow_time.hour == 8 and moscow_time.minute == 30:
        for user_id in tgID:
            try:
                rsi = calculate_rsi(timeframe)
                screenshot, lowprice14d = get_last_5_weeks_and_low_price()
                current_price = get_price_or_change('price')
                if lowprice14d is None or current_price is None:
                    raise ValueError("Не удалось получить необходимые данные.")
                
                change_percent = round((float(current_price) - lowprice14d) / lowprice14d * 100, 2)
                buy_sell_ratio = get_buy_sell_ratio(timeframe)
                
                caption = (
                    f"ЕЖЕДНЕВНЫЙ ОТЧЁТ\n"
                    f"📉 Изменение за 14 дней: {change_percent}%\n"
                    f"📊 RSI: {rsi}\n"
                    f"📈 {buy_sell_ratio}\n"
                    f"💲 *Текущая цена BTC:* *{current_price}* USDT"
                )
                
                bot.send_message(chat_id=user_id, text=caption, parse_mode='Markdown')
                bot.send_photo(chat_id=user_id, photo=screenshot, caption=caption)
            except Exception as e:
                bot.send_message(user_id, f"⚠️ Ошибка при отправке ежедневного обновления: {e}")

schedule.every().day.at("08:30").do(daily_update)

#Запускает планировщик заданий для регулярного выполнения
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

#Мониторит RSI и отправляет уведомления при достижении порогов
def monitor_rsi(user_id):
    global rsiduplication35, rsiduplication30, rsiduplication70, rsiduplication60
    while True:
        try:
            rsihour = float(calculate_rsi(timeframe))
            thresholds = {30: rsiduplication30, 35: rsiduplication35, 60: rsiduplication60, 70: rsiduplication70}
            for threshold in thresholds:
                if (rsihour < threshold and thresholds[threshold]) or (rsihour > threshold and not thresholds[threshold]):
                    get_rsi_and_send_message(user_id)
                    globals()[f"rsiduplication{threshold}"] = not thresholds[threshold]
                    print(f"RSI: {rsihour} | Проверка порогов: {thresholds}")
            time.sleep(float(timeframe) / 2 * 10)
        except Exception as e:
            time.sleep(10)

#Обрабатывает запрос на покупку BTC от пользователя
def process_trade(message):
    user_id = message.chat.id
    amount_usdt = message.text.strip()
    
    if not amount_usdt.isdigit():
        bot.send_message(user_id, "Введите корректное число.")
        return
    try:
        order = session.place_active_order(
            category="spot",
            symbol="BTCUSDT",
            side="Buy",
            orderType="Market",
            qty=amount_usdt,
            marketUnit="quoteCoin"
        )
        bot.send_message(user_id, f"✅ Куплено BTC на {amount_usdt} USDT. Количество: {order['result']['qty']}")
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка: {e}")

#Отправляет отчет пользователю с графиками и данными
def send_report(user_id):
    try:
        rsi = calculate_rsi(timeframe)
        screenshot, lowprice14d = get_last_5_weeks_and_low_price()
        current_price = get_price_or_change('price')
        
        if not lowprice14d or not current_price:
            raise ValueError("Не удалось получить данные.")
        
        change_percent = round((float(current_price) - lowprice14d) / lowprice14d * 100, 2)
        buy_sell_ratio = get_buy_sell_ratio(timeframe)
        
        caption = f"📉 Изменение за 14 дней: {change_percent}%\n📊 RSI: {rsi}\n📈 {buy_sell_ratio}"
        bot.send_photo(chat_id=user_id, photo=screenshot, caption=caption)
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка: {e}")

#Получение RSI и отправка сообщения пользователю
def get_rsi_and_send_message(user_id):
    try:
        rsi = calculate_rsi(timeframe)
        send_report(user_id)
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении RSI: {e}")
