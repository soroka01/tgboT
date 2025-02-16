import logging
import os

# Убедитесь, что директория для логов существует
log_directory = '/qqq/www/eee/logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join(log_directory, 'bot.log'),
    filemode='w'
)

# Создание обработчика для логирования ошибок в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Добавление обработчика к логгеру
logging.getLogger().addHandler(console_handler)

# Создание обработчика для логирования предупреждений в файл
warning_handler = logging.FileHandler(os.path.join(log_directory, 'warnings.log'))
warning_handler.setLevel(logging.WARNING)
warning_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Добавление обработчика к логгеру
logging.getLogger().addHandler(warning_handler)
