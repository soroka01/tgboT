from bot_instance import bot, session
from logs.logging_config import logging

# Функция для обработки торговой операции
def process_trade(message, bot):
    user_id = message.chat.id  # Получение ID пользователя
    amount_usdt = message.text.strip()  # Получение суммы в USDT из сообщения
    
    # Проверка, что введено корректное число
    if not amount_usdt.isdigit():
        bot.send_message(user_id, "Введите корректное число.")
        return
    
    try:
        # Размещение рыночного ордера на покупку BTC
        order = session.place_active_order(
            category="spot",
            symbol="BTCUSDT",
            side="Buy",
            orderType="Market",
            qty=amount_usdt,
            marketUnit="quoteCoin"
        )
        # Отправка сообщения пользователю о успешной покупке
        bot.send_message(user_id, f"✅ Куплено BTC на {amount_usdt} USDT. Количество: {order['result']['qty']}")
    except Exception as e:
        # Логирование и отправка сообщения об ошибке
        logging.error(f"Ошибка при обработке торговой операции: {e}")
        bot.send_message(user_id, f"⚠️ Ошибка при обработке торговой операции: {e}")

# Функция для получения истории торговых операций
def get_trade_history():
    logging.info("Получение истории торговых операций")  # Логирование начала получения истории
    try:
        # Получение истории ордеров
        orders = session.get_order_history(category="spot", symbol="BTCUSDT", limit=10)
        if not orders.get('result'):
            return "История торговых операций недоступна"
        
        # Формирование строки с историей ордеров
        history = "\n".join([f"ID: {order['orderId']}, Сумма: {order['qty']}, Цена: {order['price']}, Статус: {order['status']}" for order in orders['result']])
        return history
    except Exception as e:
        # Логирование и возврат сообщения об ошибке
        logging.error(f"Ошибка при получении истории торговых операций: {e}")
        return f"Ошибка: {e}"

# Функция для получения баланса пользователя
def get_balance():
    logging.info("Получение баланса пользователя")  # Логирование начала получения баланса
    try:
        # Получение баланса кошелька
        response = session.get_wallet_balance(accountType="UNIFIED")
        if response.get('ret_code') != 0:
            raise ValueError(f"Ошибка API: {response.get('ret_msg')}")
        
        # Извлечение баланса BTC и USDT
        balances = response.get('result', {}).get('list', [])[0].get('coin', [])
        btc_balance = next((item for item in balances if item["coin"] == "BTC"), {}).get("walletBalance", "N/A")
        usdt_balance = next((item for item in balances if item["coin"] == "USDT"), {}).get("walletBalance", "N/A")
        
        return btc_balance, usdt_balance
    except Exception as e:
        # Логирование и возврат сообщения об ошибке
        logging.error(f"Ошибка при получении баланса: {e}")
        return "Ошибка при получении баланса"
