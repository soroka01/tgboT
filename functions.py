import time
import pytz
import sqlite3
import schedule
from telebot import types
from datetime import datetime
from cfg import timeframe, tgID, rsi_threshold_35, rsi_threshold_30, rsi_threshold_70, rsi_threshold_60
from logs.logging_config import logging
from features.market import get_price_or_change, get_buy_sell_ratio, get_last_5_weeks_and_low_price
from features.market import calculate_rsi
from database import load_user_data, save_user_data, load_user_alerts, save_user_alerts, load_user_rsi_alerts, save_user_rsi_alerts
from buttons import create_back_button
from bot_instance import session, bot
from buttons import create_notifications_menu

# Инициализация базы данных
def init_db():
    logging.info("Инициализация базы данных")
    try:
        conn = sqlite3.connect('/root/TgBots/Bots/rsitgbotT/users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                data TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        conn.close()

# Функции для отправки отчетов и уведомлений

# Отправка отчета пользователям
def send_report(user_id, rsi, screenshot, lowprice14d, current_price, buy_sell_ratio):
    try:
        change_percent = round((float(current_price) - lowprice14d) / lowprice14d * 100, 2)
        caption = f"📉 Изменение за 14 дней: {change_percent}%\n📊 RSI: {rsi}\n📈 {buy_sell_ratio}"
        bot.send_photo(chat_id=user_id, photo=screenshot, caption=caption)
    except Exception as e:
        logging.error(f"Ошибка при отправке отчета: {e}")
        bot.send_message(user_id, f"⚠️ Ошибка: {e}")

# Получение RSI и отправка сообщения пользователю
def get_rsi_and_send_message(user_id):
    try:
        rsi = calculate_rsi(timeframe)
        screenshot, lowprice14d = get_last_5_weeks_and_low_price()  # Вызов функции
        current_price = get_price_or_change('price')
        
        if not lowprice14d or not current_price:
            raise ValueError("Не удалось получить данные.")
        
        buy_sell_ratio = get_buy_sell_ratio(timeframe)
        send_report(user_id, rsi, screenshot, lowprice14d, current_price, buy_sell_ratio)
    
    except Exception as e:
        logging.error(f"Ошибка при получении RSI: {e}")
        bot.send_message(user_id, f"⚠️ Ошибка при получении RSI: {e}")

# Ежедневное обновлени
def daily_update():
    logging.info("Запуск ежедневного обновления")
    moscow_time = get_moscow_time()
    if moscow_time.hour == 8 and moscow_time.minute == 30:
        for user_id in tgID:
            get_rsi_and_send_message(user_id)

# Мониторинг RSI
def monitor_rsi(user_id):
    logging.info(f"Мониторинг RSI для user_id: {user_id}")
    global rsi_threshold_35, rsi_threshold_30, rsi_threshold_70, rsi_threshold_60
    while True:
        try:
            rsihour = float(calculate_rsi(timeframe))
            thresholds = {30: rsi_threshold_30, 35: rsi_threshold_35, 60: rsi_threshold_60, 70: rsi_threshold_70}
            for threshold in thresholds:
                if (rsihour < threshold and thresholds[threshold]) or (rsihour > threshold and not thresholds[threshold]):
                    get_rsi_and_send_message(user_id)
                    globals()[f"rsi_threshold_{threshold}"] = not thresholds[threshold]
                    logging.info(f"RSI: {rsihour} | Проверка порогов: {thresholds}")
            time.sleep(float(timeframe) / 2 * 10)
        except Exception as e:
            logging.error(f"Ошибка при мониторинге RSI для user_id {user_id}: {e}")
            time.sleep(10)

# Функции для обработки торговых операций

# Обработка торговой операции
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
        logging.error(f"Ошибка при обработке торговой операции: {e}")
        bot.send_message(user_id, f"⚠️ Ошибка при обработке торговой операции: {e}")

def get_latest_crypto_news():
    return "Последние новости о криптовалютах: ..."

def get_trade_history():
    logging.info("Получение истории торговых операций")
    try:
        orders = session.get_order_history(category="spot", symbol="BTCUSDT", limit=10)
        if not orders.get('result'):
            return "История торговых операций недоступна"
        
        history = "\n".join([f"ID: {order['orderId']}, Сумма: {order['qty']}, Цена: {order['price']}, Статус: {order['status']}" for order in orders['result']])
        return history
    except Exception as e:
        logging.error(f"Ошибка при получении истории торговых операций: {e}")
        return f"Ошибка: {e}"

def get_balance():
    logging.info("Получение баланса пользователя")
    try:
        response = session.get_wallet_balance(accountType="UNIFIED")
        if response.get('ret_code') != 0:
            raise ValueError(f"Ошибка API: {response.get('ret_msg')}")
        
        balances = response.get('result', {}).get('list', [])[0].get('coin', [])
        btc_balance = next((item for item in balances if item["coin"] == "BTC"), {}).get("walletBalance", "N/A")
        usdt_balance = next((item for item in balances if item["coin"] == "USDT"), {}).get("walletBalance", "N/A")
        
        return btc_balance, usdt_balance
    except Exception as e:
        logging.error(f"Ошибка при получении баланса: {e}")
        return "Ошибка при получении баланса"

# Функции для работы с пользователями и уведомлениями

def delete_all_price_alerts(message):
    user_id = message.chat.id
    save_user_alerts(user_id, [])
    bot.send_message(user_id, "Все подписки на уровни удалены.", reply_markup=create_back_button("notifications"))

def delete_price_alert(message):
    user_id = message.chat.id
    alerts = load_user_alerts(user_id)
    if alerts:
        alerts_text = "\n".join([f"{i+1}. {level['price']} USDT - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.send_message(user_id, f"Ваши подписки на уровни:\n{alerts_text}\n\nВведите номер подписки, которую хотите удалить:", reply_markup=create_back_button("notifications"))
        bot.register_next_step_handler(message, remove_price_alert)
    else:
        bot.send_message(user_id, "У вас нет активных подписок на уровни.", reply_markup=create_back_button("notifications"))

def remove_price_alert(message):
    user_id = message.chat.id
    try:
        alert_index = int(message.text.strip()) - 1
        alerts = load_user_alerts(user_id)
        if 0 <= alert_index < len(alerts):
            removed_alert = alerts.pop(alert_index)
            save_user_alerts(user_id, alerts)
            bot.send_message(user_id, f"Подписка на уровень {removed_alert['price']} USDT удалена.", reply_markup=create_back_button("notifications"))
        else:
            bot.send_message(user_id, "Неверный номер подписки.", reply_markup=create_back_button("notifications"))
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.", reply_markup=create_back_button("notifications"))

def list_price_alerts(message):
    user_id = message.chat.id
    alerts = load_user_alerts(user_id)
    if alerts:
        alerts_text = "\n".join([f"{i+1}. {level['price']} USDT - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.send_message(user_id, f"Ваши подписки на уровни:\n{alerts_text}", reply_markup=create_back_button("notifications"))
    else:
        bot.send_message(user_id, "У вас нет активных подписок на уровни.", reply_markup=create_back_button("notifications"))

def save_price_alert(message):
    user_id = message.chat.id
    try:
        price_level = float(message.text.strip())
        alerts = load_user_alerts(user_id)
        if len(alerts) >= 15:
            bot.send_message(user_id, "Вы не можете создать более 15 подписок на уровни.", reply_markup=create_back_button("notifications"))
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Единично", callback_data=f"alert_once_{price_level}"))
        markup.add(types.InlineKeyboardButton("Навсегда", callback_data=f"alert_permanent_{price_level}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="alert_back"))
        bot.send_message(user_id, "Выберите тип подписки:", reply_markup=markup)
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.", reply_markup=create_back_button("notifications"))

def save_rsi_alert(message):
    user_id = message.chat.id
    try:
        rsi_level = float(message.text.strip())
        alerts = load_user_rsi_alerts(user_id)
        if len(alerts) >= 15:
            bot.send_message(user_id, "Вы не можете создать более 15 подписок на уровни.", reply_markup=create_back_button("notifications"))
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"RSI < {rsi_level}", callback_data=f"rsi_alert_below_{rsi_level}"))
        markup.add(types.InlineKeyboardButton(f"RSI > {rsi_level}", callback_data=f"rsi_alert_above_{rsi_level}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="alert_back"))
        bot.send_message(user_id, "Выберите тип подписки:", reply_markup=markup)
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.", reply_markup=create_back_button("notifications"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("rsi_alert_below_"))
def rsi_alert_below_callback(call):
    user_id = call.message.chat.id
    try:
        rsi_level = float(call.data.split("_")[3])
        alerts = load_user_rsi_alerts(user_id)
        alerts.append({"level": rsi_level, "condition": "below", "permanent": False})
        save_user_rsi_alerts(user_id, alerts)
        bot.send_message(user_id, f"Подписка на уровень RSI < {rsi_level} установлена.", reply_markup=create_back_button("notifications"))
    except ValueError as e:
        logging.error(f"Ошибка при обработке уровня RSI: {e}")
        bot.send_message(user_id, "Ошибка при обработке уровня RSI.", reply_markup=create_back_button("notifications"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("rsi_alert_above_"))
def rsi_alert_above_callback(call):
    user_id = call.message.chat.id
    try:
        rsi_level = float(call.data.split("_")[3])
        alerts = load_user_rsi_alerts(user_id)
        alerts.append({"level": rsi_level, "condition": "above", "permanent": False})
        save_user_rsi_alerts(user_id, alerts)
        bot.send_message(user_id, f"Подписка на уровень RSI > {rsi_level} установлена.", reply_markup=create_back_button("notifications"))
    except ValueError as e:
        logging.error(f"Ошибка при обработке уровня RSI: {e}")
        bot.send_message(user_id, "Ошибка при обработке уровня RSI.", reply_markup=create_back_button("notifications"))

def send_message_with_logging(user_id, text, reply_markup=None):
    logging.info(f"Отправка сообщения для user_id: {user_id}")
    bot.send_message(user_id, text, reply_markup=reply_markup)

def edit_message_with_logging(call, text, reply_markup=None):
    user_id = call.message.chat.id
    logging.info(f"Редактирование сообщения для user_id: {user_id}")
    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=text, reply_markup=reply_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("alert_once_"))
def alert_once_callback(call):
    user_id = call.message.chat.id
    try:
        price_level = float(call.data.split("_")[2])
        alerts = load_user_alerts(user_id)
        alerts.append({"price": price_level, "permanent": False})
        save_user_alerts(user_id, alerts)
        edit_message_with_logging(call, f"Подписка на цену {price_level} USDT установлена.", create_back_button("notifications"))
    except ValueError as e:
        logging.error(f"Ошибка при обработке цены: {e}")
        edit_message_with_logging(call, "Ошибка при обработке цены.", create_back_button("notifications"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("alert_permanent_"))
def alert_permanent_callback(call):
    user_id = call.message.chat.id
    try:
        price_level = float(call.data.split("_")[2])
        alerts = load_user_alerts(user_id)
        alerts.append({"price": price_level, "permanent": True})
        save_user_alerts(user_id, alerts)
        edit_message_with_logging(call, f"Постоянная подписка на цену {price_level} USDT установлена.", create_back_button("notifications"))
    except ValueError as e:
        logging.error(f"Ошибка при обработке уровня цены: {e}")
        edit_message_with_logging(call, "Ошибка при обработке цены.", create_back_button("notifications"))

@bot.callback_query_handler(func=lambda call: call.data == "alert_back")
def alert_back_callback(call):
    user_id = call.message.chat.id
    logging.info(f"Возврат в меню уведомлений для user_id: {user_id}")
    edit_message_with_logging(call, "🔔 Управление уведомлениями:", create_notifications_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("rsi_alert_once_"))
def rsi_alert_once_callback(call):
    user_id = call.message.chat.id
    try:
        rsi_level = float(call.data.split("_")[3])
        alerts = load_user_rsi_alerts(user_id)
        alerts.append({"level": rsi_level, "permanent": False})
        save_user_rsi_alerts(user_id, alerts)
        bot.send_message(user_id, f"Подписка на RSI {rsi_level} установлена.", reply_markup=create_back_button("notifications"))
    except ValueError as e:
        logging.error(f"Ошибка при обработке уровня RSI: {e}")
        bot.send_message(user_id, "Ошибка при обработке RSI.", reply_markup=create_back_button("notifications"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("rsi_alert_permanent_"))
def rsi_alert_permanent_callback(call):
    user_id = call.message.chat.id
    try:
        rsi_level = float(call.data.split("_")[3])
        alerts = load_user_rsi_alerts(user_id)
        alerts.append({"level": rsi_level, "permanent": True})
        save_user_rsi_alerts(user_id, alerts)
        bot.send_message(user_id, f"Постоянная подписка на уровень RSI {rsi_level} установлена.", reply_markup=create_back_button("notifications"))
    except ValueError as e:
        logging.error(f"Ошибка при обработке уровня RSI: {e}")
        bot.send_message(user_id, "Ошибка при обработке уровня RSI.", reply_markup=create_back_button("notifications"))

def delete_rsi_alert(message):
    user_id = message.chat.id
    alerts = load_user_rsi_alerts(user_id)
    if alerts:
        alerts_text = "\n".join([f"{i+1}. {level['level']} - {'<' if level['condition'] == 'below' else '>'} - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=f"Ваши подписки на RSI:\n{alerts_text}\n\nВведите номер подписки, которую хотите удалить:", reply_markup=create_back_button("notifications"))
        bot.register_next_step_handler(message, remove_rsi_alert)
    else:
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text="У вас нет активных подписок на RSI.", reply_markup=create_back_button("notifications"))

def delete_all_rsi_alerts(message):
    user_id = message.chat.id
    save_user_rsi_alerts(user_id, [])
    bot.send_message(user_id, "Все подписки на RSI удалены.", reply_markup=create_back_button("notifications"))

def remove_rsi_alert(message):
    user_id = message.chat.id
    try:
        alert_index = int(message.text.strip()) - 1
        alerts = load_user_rsi_alerts(user_id)
        if 0 <= alert_index < len(alerts):
            removed_alert = alerts.pop(alert_index)
            save_user_rsi_alerts(user_id, alerts)
            bot.send_message(user_id, f"Подписка на уровень RSI {removed_alert['level']} удалена.", reply_markup=create_back_button("notifications"))
        else:
            bot.send_message(user_id, "Неверный номер подписки.", reply_markup=create_back_button("notifications"))
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.", reply_markup=create_back_button("notifications"))

def list_rsi_alerts(message):
    user_id = message.chat.id
    alerts = load_user_rsi_alerts(user_id)
    if alerts:
        alerts_text = "\n".join([f"{i+1}. {level['level']} - {'<' if level['condition'] == 'below' else '>'} - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.send_message(user_id, f"Ваши подписки на RSI:\n{alerts_text}", reply_markup=create_back_button("notifications"))
    else:
        bot.send_message(user_id, "У вас нет активных подписок на RSI.", reply_markup=create_back_button("notifications"))

def delete_all_alerts(message):
    user_id = message.chat.id
    save_user_alerts(user_id, [])
    save_user_rsi_alerts(user_id, [])
    bot.send_message(user_id, "Все подписки на уровни и RSI удалены.", reply_markup=create_back_button("notifications"))

# Планирование задач и запуск планировщика

def get_moscow_time():
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow_tz)
    return moscow_time

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def notifications_menu(message):
    user_id = message.chat.id
    logging.info(f"Отправка меню уведомлений для user_id: {user_id}")
    markup = create_notifications_menu()
    bot.send_message(user_id, "🔔 Управление уведомлениями:", reply_markup=markup)

def check_price_alerts():
    logging.info("Проверка уведомлений о цене")
    current_price = get_price_or_change('price')
    for user_id in tgID:
        alerts = load_user_alerts(user_id)
        for level in alerts[:]:
            if current_price >= level['price']:
                bot.send_message(user_id, f"Цена достигла уровня {level['price']} USDT. Текущая цена: {current_price} USDT.")
                if not level['permanent']:
                    alerts.remove(level)
        save_user_alerts(user_id, alerts)

@bot.callback_query_handler(func=lambda call: call.data == "delete_price_alert")
def delete_price_alert_callback(call):
    delete_price_alert(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "delete_rsi_alert")
def delete_rsi_alert_callback(call):
    delete_rsi_alert(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "delete_all_price_alerts")
def delete_all_price_alerts_callback(call):
    delete_all_price_alerts(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "delete_all_rsi_alerts")
def delete_all_rsi_alerts_callback(call):
    delete_all_rsi_alerts(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "delete_all_alerts")
def delete_all_alerts_callback(call):
    delete_all_alerts(call.message)
