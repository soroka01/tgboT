import time
import pytz
import telebot
import schedule
import functions
from telebot import types
from threading import Thread
from pybit.unified_trading import HTTP
from cfg import symb, timeframe, tgtoken, tgID, bykey, bysecret
from functions import get_price_data, get_price_or_change, calculate_rsi, get_buy_sell_ratio, get_last_5_weeks_and_low_price, get_moscow_time, daily_update, run_schedule, monitor_rsi, process_trade, send_report, get_rsi_and_send_message

bot = telebot.TeleBot(tgtoken)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    stat_button = types.KeyboardButton("📊 Стата")
    babit_button = types.KeyboardButton("💸 Бабит")
    markup.add(stat_button, babit_button)
    bot.send_message(message.chat.id, "👋 Добро пожаловать! \n\nВыберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 Стата")
def send_stat(message):
    user_id = message.chat.id
    try:
        rsi = calculate_rsi(timeframe)
        screenshot, lowprice14d = get_last_5_weeks_and_low_price()
        current_price = get_price_or_change('price')
        
        if lowprice14d is None or current_price is None:
            raise ValueError("⚠️ Не удалось получить необходимые данные.")
        
        change_percent = round((float(current_price) - lowprice14d) / lowprice14d * 100, 2)
        buy_sell_ratio = get_buy_sell_ratio(timeframe)
        
        caption = (
            f"📉 Изменение за 14 дней: {change_percent}%\n"
            f"📊 RSI: {rsi}\n"
            f"📈 {buy_sell_ratio}\n"
            f"💲 Текущая цена BTC: {current_price} USDT"
        )
        
        bot.send_photo(chat_id=user_id, photo=screenshot, caption=caption)
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении статистики: {e}")

@bot.message_handler(func=lambda message: message.text == "💸 Бабит")
def babit_menu(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    balance_button = types.KeyboardButton("💰 Баланс")
    history_button = types.KeyboardButton("📜 История")
    trade_button = types.KeyboardButton("🔄 Торговля")
    price_button = types.KeyboardButton("💲 Текущая цена BTC")
    back_button = types.KeyboardButton("🔙")
    markup.add(balance_button, history_button, trade_button, price_button, back_button)
    bot.send_message(user_id, "🛠️ Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔙")
def go_back_to_main_menu(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    stat_button = types.KeyboardButton("📊 Стата")
    babit_button = types.KeyboardButton("💸 Бабит")
    markup.add(stat_button, babit_button)
    bot.send_message(user_id, "🔙 Возврат к начальному меню. Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💰 Баланс")
def get_balance(message):
    user_id = message.chat.id
    try:
        session = HTTP(testnet=True, api_key=bykey, api_secret=bysecret)
        btc_balance = session.get_wallet_balance(accountType="UNIFIED", coin="BTC")
        usdt_balance = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        
        balance_message = (
            f"💰 *Ваш баланс:*\n"
            f"• BTC: *{btc_balance}*\n"
            f"• USDT: *{usdt_balance}*"
        )
        
        bot.send_message(user_id, balance_message, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении баланса: {e}")

@bot.message_handler(func=lambda message: message.text == "📜 История")
def send_history(message):
    user_id = message.chat.id
    bot.send_message(user_id, "📜 История транзакций пока недоступна.")

@bot.message_handler(func=lambda message: message.text == "🔄 Торговля")
def trade_btc(message):
    user_id = message.chat.id
    bot.send_message(user_id, "💵 Введите количество USDT для покупки BTC:")
    bot.register_next_step_handler(message, process_trade)

@bot.message_handler(func=lambda message: message.text == "💲 Текущая цена BTC")
def send_current_price(message):
    user_id = message.chat.id
    try:
        current_price = get_price_or_change('price')
        bot.send_message(user_id, f"💲 Текущая цена BTC: {current_price} USDT", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении текущей цены: {e}")        

schedule.every().minute.do(daily_update)

# Запуск планировщика в отдельном потоке
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule_thread = Thread(target=run_schedule)
schedule_thread.start()

if __name__ == '__main__':
    bot.polling(none_stop=True)
