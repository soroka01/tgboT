# Telegram Bot for Crypto Trading and Analysis

Этот проект представляет собой Telegram-бота для анализа и торговли криптовалютами, используя API Bybit и Telegram. Бот предоставляет информацию о текущих ценах, индексе относительной силы (RSI), соотношении покупок и продаж, а также позволяет пользователям выполнять торговые операции.

## Установка

1. Клонируйте репозиторий:
    ```sh
    git clone https://github.com/yourusername/yourrepository.git
    cd yourrepository
    ```

2. Создайте виртуальное окружение и активируйте его:
    ```sh
    python -m venv venv
    source venv/bin/activate  # Для Windows: venv\Scripts\activate
    ```

3. Установите зависимости:
    ```sh
    pip install -r requirements.txt
    ```

4. Настройте файл [cfg.py](http://_vscodecontentref_/0) с вашими данными:
    ```python
    symb = "BTCUSDT"
    timeframe = 60
    tgtoken = 'YOUR_TELEGRAM_BOT_TOKEN'
    tgID = [YOUR_TELEGRAM_USER_ID]
    bykey = 'YOUR_BYBIT_API_KEY'
    bysecret = 'YOUR_BYBIT_API_SECRET'
    ```

## Использование

Запустите бота:
```sh
python main.py
```
