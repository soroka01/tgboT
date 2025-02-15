from features.market import get_price_or_change
from telebot import types
from bot_instance import bot

# Функция для конвертации валют
def get_converted_amount(amount, from_currency, to_currency):
    current_price = get_price_or_change('price')
    if current_price is None:
        return "Данные недоступны"
        
    conversions = {
        ("USD", "BTC"): amount / current_price,
        ("BTC", "USD"): amount * current_price
    }
    
    return conversions.get((from_currency, to_currency), "Неподдерживаемая конвертация")

# Функция для отображения меню конвертации
def converter_menu(message):
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    buttons = [
        ("USD в BTC", "convert_usd_to_btc"),
        ("BTC в USD", "convert_btc_to_usd"),
        ("🔙 Назад", "back_to_menu")
    ]
    
    for text, callback_data in buttons:
        markup.add(types.InlineKeyboardButton(text, callback_data=callback_data))
    
    bot.send_message(user_id, "Выберите конвертацию:", reply_markup=markup)
