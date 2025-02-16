from telebot import types
from database import load_user_alerts, save_user_alerts
from buttons import create_back_button
from logs.logging_config import logging

def save_alert(message, bot, alert_type):
    user_id = message.chat.id
    logging.info(f"Сохранение уведомления {alert_type} для user_id: {user_id}")
    try:
        level = float(message.text.strip())
        alerts = load_user_alerts(user_id)
        if len(alerts) >= 15:
            bot.send_message(user_id, "Вы не можете создать более 15 подписок на уровни.", reply_markup=create_back_button("notifications"))
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Единично", callback_data=f"{alert_type}_alert_once_{level}"))
        markup.add(types.InlineKeyboardButton("Навсегда", callback_data=f"{alert_type}_alert_permanent_{level}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="alert_back"))
        bot.send_message(user_id, "Выберите тип подписки:", reply_markup=markup)
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.", reply_markup=create_back_button("notifications"))

def delete_alert(message, bot, alert_type):
    user_id = message.chat.id
    logging.info(f"Удаление уведомления {alert_type} для user_id: {user_id}")
    alerts = load_user_alerts(user_id)
    if alerts:
        alerts_text = "\n".join([f"{i+1}. {level[alert_type]} - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.send_message(user_id, f"Ваши подписки на уровни:\n{alerts_text}\n\nВведите номер подписки, которую хотите удалить:", reply_markup=create_back_button("notifications"))
        bot.register_next_step_handler(message, lambda msg: remove_alert(msg, bot, alert_type))
    else:
        bot.send_message(user_id, "У вас нет активных подписок на уровни.", reply_markup=create_back_button("notifications"))

def remove_alert(message, bot, alert_type):
    user_id = message.chat.id
    logging.info(f"Удаление уведомления {alert_type} для user_id: {user_id}")
    try:
        alert_index = int(message.text.strip()) - 1
        alerts = load_user_alerts(user_id)
        if 0 <= alert_index < len(alerts):
            removed_alert = alerts.pop(alert_index)
            save_user_alerts(user_id, alerts)
            bot.send_message(user_id, f"Подписка на уровень {removed_alert[alert_type]} удалена.", reply_markup=create_back_button("notifications"))
        else:
            bot.send_message(user_id, "Неверный номер подписки.", reply_markup=create_back_button("notifications"))
    except ValueError:
        bot.send_message(user_id, "Введите корректное число.", reply_markup=create_back_button("notifications"))

def list_alerts(message, bot, alert_type):
    user_id = message.chat.id
    alerts = load_user_alerts(user_id)
    if alerts:
        alerts_text = "\n".join([f"{i+1}. {level[alert_type]} - {'Навсегда' if level['permanent'] else 'Единично'}" for i, level in enumerate(alerts)])
        bot.send_message(user_id, f"Ваши подписки на уровни:\n{alerts_text}", reply_markup=create_back_button("notifications"))
    else:
        bot.send_message(user_id, "У вас нет активных подписок на уровни.", reply_markup=create_back_button("notifications"))

def delete_all_alerts(message, bot):
    user_id = message.chat.id
    logging.info(f"Удаление всех уведомлений для user_id: {user_id}")
    save_user_alerts(user_id, [])
    bot.send_message(user_id, "Все подписки на уровни удалены.", reply_markup=create_back_button("notifications"))
