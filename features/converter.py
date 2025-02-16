from features.market import get_price_or_change
from telebot import types
from bot_instance import bot
import telebot

# Функция для конвертации валют
def get_converted_amount(amount, from_currency, to_currency):
    current_price = get_price_or_change('price')
    if current_price is None:
        return "Данные недоступны"
    
    conversions = {
        ("USD", "BTC"): amount / current_price,
        ("BTC", "USD"): amount * current_price
    }
    
    converted_amount = conversions.get((from_currency, to_currency), "Неподдерживаемая конвертация")
    if isinstance(converted_amount, float):
        return round(converted_amount, 3)
    return converted_amount

# Функция для отображения меню конвертации
def converter_menu(message):
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="USD в BTC", callback_data="convert_usd_to_btc"),
        types.InlineKeyboardButton(text="BTC в USD", callback_data="convert_btc_to_usd"),
        types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    ]
    
    markup.add(*buttons)
    
    try:
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text="Выберите конвертацию:", reply_markup=markup)
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            bot.edit_message_reply_markup(chat_id=user_id, message_id=message.message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id=user_id, text="Выберите конвертацию:", reply_markup=markup)
