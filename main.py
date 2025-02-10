import os
import time
import pytz
import json
import telebot
import schedule
from telebot import types
from threading import Thread
from pybit.unified_trading import HTTP
from cfg import symb, timeframe, tgtoken, tgID, bykey, bysecret
from functions import get_price_data, get_price_or_change, calculate_rsi, get_buy_sell_ratio, get_last_5_weeks_and_low_price, get_moscow_time, daily_update, monitor_rsi, process_trade, send_report, get_rsi_and_send_message, save_user_data, load_user_data, save_user_alerts, load_user_alerts, get_latest_crypto_news, get_converted_amount

# Создание бота
bot = telebot.TeleBot(tgtoken)

# Константы для сообщений
WELCOME_MESSAGE = "👋 Добро пожаловать!\nПомощь тут: /help\n\nВыберите действие:"
HELP_MESSAGE = (
    "Доступные команды:\n"
    "/start - Начало работы с ботом\n"
    "/help - Список доступных команд\n"
    "📊 Стата - Получить статистику\n"
    "💸 Бабит - Меню для торговли\n"
    "🔔 Уведомления - Управление уведомлениями\n"
    "👤 Аккаунт - Информация об аккаунте\n"
)

# Функции для работы с пользователями и уведомлениями

def delete_all_price_alerts(message):
    user_id = message.chat.id
    save_user_alerts(user_id, [])
    bot.send_message(user_id, "Все подписки на уровни удалены.")

def delete_price_alert(message):
    user_id = message.chat.id
    alerts = load_user_alerts(user_id)
    if alerts:
        # Вывод списка подписок перед запросом номера для удаления
        alerts_text = "\n".join([f"{i+1}. {level['price']} USDT - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.send_message(user_id, f"Ваши подписки на уровни:\n{alerts_text}\n\nВведите номер подписки, которую хотите удалить:")
        bot.register_next_step_handler(message, remove_price_alert)
    else:
        bot.send_message(user_id, "У вас нет активных подписок на уровни.")

def remove_price_alert(message):
    user_id = message.chat.id
    try:
        alert_index = int(message.text.strip()) - 1
        alerts = load_user_alerts(user_id)
        if 0 <= alert_index < len(alerts):
            removed_alert = alerts.pop(alert_index)
            save_user_alerts(user_id, alerts)
            bot.send_message(user_id, f"Подписка на уровень {removed_alert['price']} USDT удалена.")
        else:
            bot.send_message(user_id, "Неверный номер подписки.")
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.")

def list_price_alerts(message):
    user_id = message.chat.id
    alerts = load_user_alerts(user_id)
    if alerts:
        alerts_text = "\n".join([f"{i+1}. {level['price']} USDT - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.send_message(user_id, f"Ваши подписки на уровни:\n{alerts_text}")
    else:
        bot.send_message(user_id, "У вас нет активных подписок на уровни.")

def save_price_alert(message):
    user_id = message.chat.id
    try:
        price_level = float(message.text.strip())
        alerts = load_user_alerts(user_id)
        if len(alerts) >= 15:
            bot.send_message(user_id, "Вы не можете создать более 15 подписок на уровни.")
            return
        # Создание кнопок для выбора типа подписки
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Единично", callback_data=f"alert_once_{price_level}"))
        markup.add(types.InlineKeyboardButton("Навсегда", callback_data=f"alert_permanent_{price_level}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="alert_back"))
        bot.send_message(user_id, "Выберите тип подписки:", reply_markup=markup)
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("alert_"))
def handle_alert_callback(call):
    user_id = call.message.chat.id
    data = call.data.split("_")
    action = data[1]
    price_level = float(data[2])
    alerts = load_user_alerts(user_id)
    if action == "once":
        alerts.append({'price': price_level, 'permanent': False})
        bot.send_message(user_id, f"Уведомление установлено на уровне {price_level} USDT (единично).")
    elif action == "permanent":
        alerts.append({'price': price_level, 'permanent': True})
        bot.send_message(user_id, f"Уведомление установлено на уровне {price_level} USDT (навсегда).")
    elif action == "back":
        bot.send_message(user_id, "Введите ценовой уровень для уведомления:")
        bot.register_next_step_handler(call.message, save_price_alert)
    
    # Сохранение обновленного списка подписок
    save_user_alerts(user_id, alerts)
    
    # Удаление кнопок
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

def check_price_alerts():
    current_price = get_price_or_change('price')
    for user_id in tgID:
        alerts = load_user_alerts(user_id)
        for level in alerts[:]:
            if current_price >= level['price']:
                bot.send_message(user_id, f"Цена достигла уровня {level['price']} USDT. Текущая цена: {current_price} USDT.")
                if not level['permanent']:
                    alerts.remove(level)
        save_user_alerts(user_id, alerts)

def change_user_name(message):
    user_id = message.chat.id
    new_name = message.text.strip()
    user_data = load_user_data(user_id)
    user_data["name"] = new_name
    save_user_data(user_id, user_data)
    bot.send_message(user_id, f"Ваше имя успешно изменено на: {new_name}")

# Обработчики команд и сообщений

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.text == "/start":
        # Создание кнопок для главного меню
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        stat_button = types.KeyboardButton("📊 Стата")
        babit_button = types.KeyboardButton("💸 Бабит")
        alert_button = types.KeyboardButton("🔔 Уведомления")
        account_button = types.KeyboardButton("👤 Аккаунт")
        markup.add(stat_button, babit_button, alert_button, account_button)
        bot.send_message(message.chat.id, WELCOME_MESSAGE, reply_markup=markup)
    elif message.text == "/help":
        bot.send_message(message.chat.id, HELP_MESSAGE)

@bot.message_handler(func=lambda message: message.text == "📊 Стата")
def send_stat(message):
    user_id = message.chat.id
    try:
        # Получение данных для статистики
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
        
        # Отправка фото с данными
        bot.send_photo(chat_id=user_id, photo=screenshot, caption=caption)
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении статистики: {e}")

@bot.message_handler(func=lambda message: message.text == "💸 Бабит")
def babit_menu(message):
    user_id = message.chat.id
    # Создание кнопок для меню "Бабит"
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    balance_button = types.KeyboardButton("💰 Баланс")
    history_button = types.KeyboardButton("📜 История")
    trade_button = types.KeyboardButton("🔄 Торговля")
    price_button = types.KeyboardButton("💲 Текущая цена BTC")
    back_button = types.KeyboardButton("🔙")
    markup.add(balance_button, history_button, trade_button, price_button, back_button)
    bot.send_message(user_id, "🛠️ Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔙")
def cancel_trade(message):
    user_id = message.chat.id
    # Возврат к главному меню
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    stat_button = types.KeyboardButton("📊 Стата")
    babit_button = types.KeyboardButton("💸 Бабит")
    alert_button = types.KeyboardButton("🔔 Уведомления")
    account_button = types.KeyboardButton("👤 Аккаунт")
    markup.add(stat_button, babit_button, alert_button, account_button)
    bot.send_message(user_id, "🔙 Возврат к начальному меню. Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💰 Баланс")
def get_balance(message):
    user_id = message.chat.id
    try:
        # Получение баланса пользователя
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
    # Создание кнопки "Назад"
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    back_button = types.KeyboardButton("🔙")
    markup.add(back_button)
    bot.send_message(user_id, "💵 Введите количество USDT для покупки BTC:", reply_markup=markup)
    bot.register_next_step_handler(message, process_trade)

@bot.message_handler(func=lambda message: message.text == "💲 Текущая цена BTC")
def send_current_price(message):
    user_id = message.chat.id
    try:
        # Получение текущей цены BTC
        current_price = get_price_or_change('price')
        bot.send_message(user_id, f"💲 Текущая цена BTC: {current_price} USDT", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении текущей цены: {e}")

@bot.message_handler(func=lambda message: message.text == "🔔 Уведомления")
def notifications_menu(message):
    user_id = message.chat.id
    # Создание кнопок для меню "Уведомления"
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    set_alert_button = types.KeyboardButton("🔔 Установить уведомление")
    list_alerts_button = types.KeyboardButton("📋 Список уведомлений")
    delete_alert_button = types.KeyboardButton("❌ Удалить уведомление")
    delete_all_alerts_button = types.KeyboardButton("❌ Удалить все уведомления")
    back_button = types.KeyboardButton("🔙")
    markup.add(set_alert_button, list_alerts_button, delete_alert_button, delete_all_alerts_button, back_button)
    bot.send_message(user_id, "🔔 Управление уведомлениями:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔔 Установить уведомление")
def set_alert(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Введите ценовой уровень для уведомления:")
    bot.register_next_step_handler(message, save_price_alert)

@bot.message_handler(func=lambda message: message.text == "📋 Список уведомлений")
def list_alerts(message):
    list_price_alerts(message)

@bot.message_handler(func=lambda message: message.text == "❌ Удалить уведомление")
def delete_alert(message):
    delete_price_alert(message)

@bot.message_handler(func=lambda message: message.text == "❌ Удалить все уведомления")
def delete_all_alerts(message):
    delete_all_price_alerts(message)

@bot.message_handler(func=lambda message: message.text == "👤 Аккаунт")
def account_info(message):
    user_id = message.chat.id
    user_data = load_user_data(user_id)
    user_name = user_data.get("name", "Не установлено")
    
    try:
        # Получение баланса пользователя
        session = HTTP(testnet=True, api_key=bykey, api_secret=bysecret)
        btc_balance = session.get_wallet_balance(accountType="UNIFIED", coin="BTC")
        usdt_balance = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        
        balance_message = (
            f"💰 *Ваш баланс:*\n"
            f"• BTC: *{btc_balance}*\n"
            f"• USDT: *{usdt_balance}*"
        )
    except Exception as e:
        balance_message = f"⚠️ Ошибка при получении баланса: {e}"
    
    account_message = (
        f"👤 *Ваш аккаунт:*\n"
        f"• ID: *{user_id}*\n"
        f"• Имя: *{user_name}*\n\n"
        f"{balance_message}"
    )
    
    # Создание кнопок "Изменить имя" и "Назад"
    markup = types.InlineKeyboardMarkup()
    change_name_button = types.InlineKeyboardButton("Изменить имя", callback_data="change_name")
    back_button = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
    markup.add(change_name_button, back_button)
    
    bot.send_message(user_id, account_message, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "change_name")
def change_name_callback(call):
    user_id = call.message.chat.id
    bot.send_message(user_id, "Введите новое имя:")
    bot.register_next_step_handler(call.message, change_user_name)
    # Удаление кнопок
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu_callback(call):
    user_id = call.message.chat.id
    # Возврат к главному меню
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    stat_button = types.KeyboardButton("📊 Стата")
    babit_button = types.KeyboardButton("💸 Бабит")
    alert_button = types.KeyboardButton("🔔 Уведомления")
    account_button = types.KeyboardButton("👤 Аккаунт")
    markup.add(stat_button, babit_button, alert_button, account_button)
    bot.send_message(user_id, "🔙 Возврат к начальному меню. Выберите действие:", reply_markup=markup)
    # Удаление кнопок
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

# Планирование задач
schedule.every().minute.do(daily_update)
schedule.every().minute.do(check_price_alerts)

# Запуск планировщика в отдельном потоке
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule_thread = Thread(target=run_schedule)
schedule_thread.start()

if __name__ == '__main__':
    bot.polling(none_stop=True)
