import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

symb = "BTCUSDT"
timeframe = 60
tgtoken = os.getenv('TG_TOKEN')
tgID = [1111, 1111, 1111]
bysecret = os.getenv('BY_SECRET', '')
bykey = os.getenv('BY_KEY', '')

# Переменные для RSI
rsi_thresholds = {
    '35': True,
    '30': True,
    '70': False,
    '60': False
}

rsi_threshold_35 = 35
rsi_threshold_30 = 30
rsi_threshold_70 = 70
rsi_threshold_60 = 60
