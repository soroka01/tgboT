from telebot import types
from logs.logging_config import logging

def create_markup(buttons):
    markup = types.InlineKeyboardMarkup()
    for button in buttons:
        markup.add(types.InlineKeyboardButton(button["text"], callback_data=button["callback_data"]))
    return markup

def create_back_button(menu):
    return create_markup([{"text": "🔙 Назад", "callback_data": f"back_to_{menu}"}])

def create_main_menu():
    buttons = [
        {"text": "📊 Стата", "callback_data": "stat"},
        {"text": "💸 Бабит", "callback_data": "babit"},
        {"text": "🔔 Уведомления", "callback_data": "notifications"},
        {"text": "👤 Аккаунт", "callback_data": "account"},
        {"text": "📰 Новости", "callback_data": "news"},
        {"text": "💱 Конвертер", "callback_data": "converter"}
    ]
    return create_markup(buttons)

def create_babit_menu():
    buttons = [
        {"text": "💰 Баланс", "callback_data": "balance"},
        {"text": "📜 История", "callback_data": "history"},
        {"text": "🔄 Торговля", "callback_data": "trade"},
        {"text": "💲 Текущая цена BTC", "callback_data": "current_price"},
        {"text": "🔙 Назад", "callback_data": "back_to_menu"}
    ]
    return create_markup(buttons)

def create_notifications_menu():
    buttons = [
        {"text": "🔔 Установить уведомление на цену", "callback_data": "set_price_alert"},
        {"text": "📋 Список уведомлений на цену", "callback_data": "list_price_alerts"},
        {"text": "🔔 Установить уведомление на RSI", "callback_data": "set_rsi_alert"},
        {"text": "📋 Список уведомлений на RSI", "callback_data": "list_rsi_alerts"},
        {"text": "❌ Удалить уведомление на цену", "callback_data": "delete_price_alert"},
        {"text": "❌ Удалить уведомление на RSI", "callback_data": "delete_rsi_alert"},
        {"text": "❌ Удалить все уведомления на цену", "callback_data": "delete_all_price_alerts"},
        {"text": "❌ Удалить все уведомления на RSI", "callback_data": "delete_all_rsi_alerts"},
        {"text": "❌ Удалить все ", "callback_data": "delete_all_alerts"},
        {"text": "🔙 Назад", "callback_data": "back_to_menu"}
    ]
    return create_markup(buttons)

def create_account_menu():
    buttons = [
        {"text": "Изменить имя", "callback_data": "change_name"},
        {"text": "🔙 Назад", "callback_data": "back_to_menu"}
    ]
    return create_markup(buttons)

def create_rsi_menu():
    buttons = [
        {"text": "30", "callback_data": "rsi_30"},
        {"text": "35", "callback_data": "rsi_35"},
        {"text": "60", "callback_data": "rsi_60"},
        {"text": "70", "callback_data": "rsi_70"},
        {"text": "🔙 Назад", "callback_data": "back_to_notifications"}
    ]
    return create_markup(buttons)

def create_converter_menu():
    buttons = [
        {"text": "USD в BTC", "callback_data": "usd_to_btc"},
        {"text": "BTC в USD", "callback_data": "btc_to_usd"},
        {"text": "🔙 Назад", "callback_data": "back_to_menu"}
    ]
    return create_markup(buttons)
