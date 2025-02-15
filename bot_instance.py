import telebot
from pybit.unified_trading import HTTP
from cfg import tgtoken, bykey, bysecret

# Создание глобального объекта сессии для работы с Bybit API
session = HTTP(testnet=False, api_key=bykey, api_secret=bysecret)

# Создание бота
bot = telebot.TeleBot(tgtoken)
