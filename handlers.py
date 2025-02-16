import telebot
from features.trade import process_trade, get_trade_history, get_balance as fetch_balance
from features.market import get_price_or_change, get_buy_sell_ratio, get_last_5_weeks_and_low_price
from buttons import create_back_button, create_main_menu, create_babit_menu, create_account_menu, create_notifications_menu
from features.converter import converter_menu
from features.market import calculate_rsi, get_price_or_change
from database import load_user_data
from features.news import get_latest_crypto_news
from cfg import timeframe
from features.converter import get_converted_amount, get_price_or_change
from logs.logging_config import logging
from functions import save_price_alert, save_rsi_alert, list_price_alerts, list_rsi_alerts, delete_price_alert, delete_all_price_alerts, get_price_or_change, get_buy_sell_ratio, get_last_5_weeks_and_low_price, calculate_rsi, delete_all_rsi_alerts, delete_rsi_alert 

# Сообщения приветствия и помощи
WELCOME_MESSAGE = "👋 Добро пожаловать!\nПомощь тут: /help\nВыберите действие:"
HELP_MESSAGE = "Доступные команды:\n/start - Начало работы с ботом\n/help - Список доступных команд\n📊 Стата - Получить статистику\n💸 Бабит - Меню для торговли\n🔔 Уведомления - Управление уведомлениями\n👤 Аккаунт - Информация об аккаунте\n📰 Новости - Последние новости о криптовалютах\n💱 Конвертер - Конвертация валют"

# Регистрация обработчиков для бота
def register_handlers(bot, session):
    # Отправка сообщения с логированием
    def send_message_with_logging(user_id, text, reply_markup=None):
        logging.info(f"Отправка сообщения для user_id: {user_id}")
        bot.send_message(user_id, text, reply_markup=reply_markup)

    # Редактирование сообщения с логированием
    def edit_message_with_logging(call, text=None, reply_markup=None):
        user_id = call.message.chat.id
        logging.info(f"Редактирование сообщения для user_id: {user_id}")
        try:
            if text:
                bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=text, reply_markup=reply_markup)
            else:
                bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=reply_markup)
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                logging.warning(f"Сообщение для user_id: {user_id} не изменено, так как содержимое и разметка те же самые.")
            elif "there is no text in the message to edit" in str(e):
                logging.warning(f"Сообщение для user_id: {user_id} не содержит текста для редактирования.")
            else:
                raise e

    # Обработчик команд /start и /help
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user_id = message.chat.id
        logging.info(f"Обработка команды {message.text} для user_id: {user_id}")
        if message.text == "/start":
            send_message_with_logging(user_id, WELCOME_MESSAGE, create_main_menu())
        elif message.text == "/help":
            send_message_with_logging(user_id, HELP_MESSAGE, create_back_button("menu"))

    # Обработчик callback данных
    @bot.callback_query_handler(func=lambda call: call.data in ["stat", "babit", "notifications", "account", "news", "converter"])
    def handle_callbacks(call):
        user_id = call.message.chat.id
        logging.info(f"Обработка callback data {call.data} для user_id: {user_id}")
        if call.data == "stat":
            send_stat(call.message)
        elif call.data == "babit":
            edit_message_with_logging(call, "🛠️ Выберите действие:", create_babit_menu())
        elif call.data == "notifications":
            edit_message_with_logging(call, "🔔 Управление уведомлениями:", create_notifications_menu())
        elif call.data == "account":
            account_info(call.message)
        elif call.data == "news":
            send_news(call.message)
        elif call.data == "converter":
            edit_message_with_logging(call, "Выберите конвертацию:", converter_menu(call.message))

    # Обработчик callback данных для уведомлений
    @bot.callback_query_handler(func=lambda call: call.data in ["set_price_alert", "list_price_alerts", "set_rsi_alert", "list_rsi_alerts", "delete_alert", "delete_all_alerts"])
    def handle_notification_callbacks(call):
        user_id = call.message.chat.id
        logging.info(f"Обработка callback data {call.data} для user_id: {user_id}")
        if call.data == "set_price_alert":
            bot.send_message(user_id, "Введите уровень цены для уведомления:")
            bot.register_next_step_handler(call.message, save_price_alert)
        elif call.data == "list_price_alerts":
            list_price_alerts(call.message)
        elif call.data == "set_rsi_alert":
            bot.send_message(user_id, "Введите уровень RSI для уведомления:")
            bot.register_next_step_handler(call.message, save_rsi_alert)
        elif call.data == "list_rsi_alerts":
            list_rsi_alerts(call.message)
        elif call.data == "delete_alert":
            delete_price_alert(call.message)
        elif call.data == "delete_all_alerts":
            delete_all_price_alerts(call.message)

    # Обработчик callback данных для возврата в меню
    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_"))
    def back_to_menu_callback(call):
        user_id = call.message.chat.id
        logging.info(f"Обработка callback data {call.data} для user_id: {user_id}")
        bot.clear_step_handler_by_chat_id(chat_id=user_id)  # Остановить ожидание следующего сообщения
        menu = call.data.split("_")[2]
        if menu == "menu":
            edit_message_with_logging(call, WELCOME_MESSAGE, create_main_menu())
        elif menu == "babit":
            edit_message_with_logging(call, "🛠️ Выберите действие:", create_babit_menu())
        elif menu == "notifications":
            edit_message_with_logging(call, "🔔 Управление уведомлениями:", create_notifications_menu())
        elif menu == "account":
            account_info(call.message)
        elif menu == "converter":
            edit_message_with_logging(call, "Выберите конвертацию:", converter_menu(call.message))
        elif menu == "news":
            send_news(call.message)

    @bot.callback_query_handler(func=lambda call: call.data in ["balance", "history", "trade", "current_price"])
    def handle_babit_callbacks(call):
        user_id = call.message.chat.id
        logging.info(f"Обработка callback data {call.data} для user_id: {user_id}")
        if call.data == "balance":
            get_balance(call.message)
        elif call.data == "history":
            send_history(call.message)
        elif call.data == "trade":
            trade_btc(call)
        elif call.data == "current_price":
            send_current_price(call.message)

    # Обработчик callback данных для конвертера
    @bot.callback_query_handler(func=lambda call: call.data in ["convert_usd_to_btc", "convert_btc_to_usd"])
    def handle_converter_callbacks(call):
        user_id = call.message.chat.id
        logging.info(f"Обработка callback data {call.data} для user_id: {user_id}")
        if call.data == "convert_usd_to_btc":
            bot.send_message(user_id, "Введите количество USD для конвертации в BTC:")
            bot.register_next_step_handler(call.message, lambda msg: convert_currency(msg, "USD", "BTC"))
        elif call.data == "convert_btc_to_usd":
            bot.send_message(user_id, "Введите количество BTC для конвертации в USD:")
            bot.register_next_step_handler(call.message, lambda msg: convert_currency(msg, "BTC", "USD"))

    # Функция для конвертации валют
    def convert_currency(message, from_currency, to_currency):
        user_id = message.chat.id
        try:
            amount = float(message.text.strip())
            converted_amount = get_converted_amount(amount, from_currency, to_currency)
            bot.send_message(user_id, f"Конвертированная сумма: {converted_amount} {to_currency}", reply_markup=create_back_button("converter"))
        except ValueError:
            bot.send_message(user_id, "Введите корректное число.", reply_markup=create_back_button("converter"))

    # Обработчик текстовых сообщений
    @bot.message_handler(func=lambda message: message.text in ["📊 Стата", "💸 Бабит", "💰 Баланс", "📜 История", "🔄 Торговля", "💲 Текущая цена BTC", "🔔 Уведомления", "👤 Аккаунт", "📰 Новости"])
    def handle_messages(message):
        user_id = message.chat.id
        logging.info(f"Обработка сообщения {message.text} для user_id: {user_id}")
        if message.text == "📊 Стата":
            send_stat(message)
        elif message.text == "💸 Бабит":
            babit_menu(message)
        elif message.text == "💰 Баланс":
            get_balance(message)
        elif message.text == "📜 История":
            send_history(message)
        elif message.text == "🔄 Торговля":
            trade_btc(message)
        elif message.text == "💲 Текущая цена BTC":
            send_current_price(message)
        elif message.text == "🔔 Уведомления":
            notifications_menu(message)
        elif message.text == "👤 Аккаунт":
            account_info(message)
        elif message.text == "📰 Новости":
            send_news(message)

    # Отправка статистики
    def send_stat(message):
        user_id = message.chat.id
        logging.info(f"Отправка статистики для user_id: {user_id}")
        try:
            rsi = calculate_rsi(timeframe)
            screenshot = None  # Сброс переменной перед новым вызовом
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
            logging.info(f"Размер изображения: {screenshot.getbuffer().nbytes} байт")
            bot.send_photo(chat_id=user_id, photo=screenshot, caption=caption)
        except Exception as e:
            logging.error(f"Ошибка при отправке статистики для user_id {user_id}: {e}")
            send_message_with_logging(user_id, f"⚠️ Ошибка при получении статистики: {e}")

    # Отправка меню Бабит
    def babit_menu(message):
        user_id = message.chat.id
        logging.info(f"Отправка меню Бабит для user_id: {user_id}")
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text="🛠️ Выберите действие:", reply_markup=create_babit_menu())

    # Получение баланса
    def get_balance(message):
        user_id = message.chat.id
        logging.info(f"Получение баланса для user_id: {user_id}")
        try:
            btc_balance, usdt_balance = fetch_balance()  # Вызов функции get_balance из features.trade
            balance_message = (
                f"💰 Ваш баланс:\n"
                f"• BTC: {btc_balance}\n"
                f"• USDT: {usdt_balance}"
            )
            bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=balance_message, reply_markup=create_back_button("babit"))
        except Exception as e:
            logging.error(f"Ошибка при получении баланса для user_id {user_id}: {e}")
            bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=f"⚠️ Ошибка при получении баланса: {e}", reply_markup=create_back_button("babit"))

    # Отправка истории операций
    def send_history(message):
        user_id = message.chat.id
        logging.info(f"Отправка истории операций для user_id: {user_id}")
        try:
            history = get_trade_history()
            bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=f"📜 История операций:\n\n{history}", reply_markup=create_back_button("babit"))
        except Exception as e:
            logging.error(f"Ошибка при получении истории операций для user_id {user_id}: {e}")
            bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=f"⚠️ Ошибка при получении истории операций: {e}", reply_markup=create_back_button("babit"))

    # Запрос на ввод количества USDT для покупки BTC
    def trade_btc(call):
        user_id = call.message.chat.id
        logging.info(f"Запрос на ввод количества USDT для user_id: {user_id}")
        markup = create_back_button("babit")
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="💵 Введите количество USDT для покупки BTC:", reply_markup=markup)
        bot.register_next_step_handler(call.message, lambda msg: process_trade(msg, bot))

    # Отправка текущей цены BTC
    def send_current_price(message):
        user_id = message.chat.id
        logging.info(f"Отправка текущей цены BTC для user_id: {user_id}")
        try:
            current_price = get_price_or_change('price')
            bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=f"💲 Текущая цена BTC: {current_price} USDT", reply_markup=create_back_button("babit"))
        except Exception as e:
            logging.error(f"Ошибка при получении текущей цены для user_id {user_id}: {e}")
            bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=f"⚠️ Ошибка при получении текущей цены: {e}", reply_markup=create_back_button("babit"))

    # Отправка меню уведомлений
    def notifications_menu(message):
        user_id = message.chat.id
        logging.info(f"Отправка меню уведомлений для user_id: {user_id}")
        markup = create_notifications_menu()
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text="🔔 Управление уведомлениями:", reply_markup=markup)

    # Отправка информации об аккаунте
    def account_info(message):
        user_id = message.chat.id
        logging.info(f"Отправка информации об аккаунте для user_id: {user_id}")
        user_data = load_user_data(user_id)
        user_name = user_data.get("name", "Не установлено")
        try:
            response = session.get_wallet_balance(accountType="UNIFIED", coin="BTC,USDT")
            btc_balance = response['result']['list'][0]['coin'][0]['walletBalance']
            usdt_balance = response['result']['list'][0]['coin'][1]['walletBalance']
            balance_message = (
                f"💰 Ваш баланс:\n"
                f"• BTC: {btc_balance}\n"
                f"• USDT: {usdt_balance}"
            )
        except Exception as e:
            logging.error(f"Ошибка при получении баланса для user_id {user_id}: {e}")
            balance_message = f"⚠️ Ошибка при получении баланса: {e}"
        account_message = (
            f"👤 Ваш аккаунт:\n"
            f"• ID: {user_id}\n"
            f"• Имя: {user_name}\n\n"
            f"{balance_message}"
        )
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=account_message, reply_markup=create_account_menu())

    # Отправка новостей
    def send_news(message):
        user_id = message.chat.id
        logging.info(f"Отправка новостей для user_id: {user_id}")
        news = get_latest_crypto_news()
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=news, reply_markup=create_back_button("menu"))

    # Отправка уведомления RSI
    def send_rsi_notification(message):
        logging.info(f"Отправка уведомления RSI для user_id: {message.chat.id}")
        send_stat(message)
    
    # Обработчик callback данных для уведомлений RSI
    @bot.callback_query_handler(func=lambda call: call.data in ["set_rsi_alert", "list_rsi_alerts", "delete_rsi_alert", "delete_all_rsi_alerts"])
    def handle_rsi_notification_callbacks(call):
        user_id = call.message.chat.id
        logging.info(f"Обработка callback data {call.data} для user_id: {user_id}")
        if call.data == "set_rsi_alert":
            bot.send_message(user_id, "Введите уровень RSI для уведомления:")
            bot.register_next_step_handler(call.message, save_rsi_alert)
        elif call.data == "list_rsi_alerts":
            list_rsi_alerts(call.message)
        elif call.data == "delete_rsi_alert":
            delete_rsi_alert(call.message)
        elif call.data == "delete_all_rsi_alerts":
            delete_all_rsi_alerts(call.message)
