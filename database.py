import sqlite3
import json
from contextlib import closing
from logs.logging_config import logging

DB_PATH = '/qqq/www/eee/users.db'

def init_db():
    logging.info("Инициализация базы данных")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        data TEXT
                    )
                ''')
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")

def load_user_data(user_id):
    logging.info(f"Загрузка данных пользователя для user_id: {user_id}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('SELECT data FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                return json.loads(row[0]) if row else {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных пользователя для user_id {user_id}: {e}")
        return {}

def save_user_data(user_id, data):
    logging.info(f"Сохранение данных пользователя для user_id: {user_id}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('INSERT OR REPLACE INTO users (user_id, data) VALUES (?, ?)', (user_id, json.dumps(data)))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных пользователя для user_id {user_id}: {e}")

def delete_user_data(user_id):
    logging.info(f"Удаление данных пользователя для user_id: {user_id}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при удалении данных пользователя для user_id {user_id}: {e}")

def load_user_alerts(user_id):
    logging.info(f"Загрузка подписок на уровни для user_id: {user_id}")
    user_data = load_user_data(user_id)
    return user_data.get("alerts", [])

def save_user_alerts(user_id, alerts):
    logging.info(f"Сохранение подписок на уровни для user_id: {user_id}")
    user_data = load_user_data(user_id)
    user_data["alerts"] = alerts
    save_user_data(user_id, user_data)

def load_user_rsi_alerts(user_id):
    logging.info(f"Загрузка подписок на RSI для user_id: {user_id}")
    user_data = load_user_data(user_id)
    return user_data.get("rsi_alerts", [])

def save_user_rsi_alerts(user_id, rsi_alerts):
    logging.info(f"Сохранение подписок на RSI для user_id: {user_id}")
    user_data = load_user_data(user_id)
    user_data["rsi_alerts"] = rsi_alerts
    save_user_data(user_id, user_data)
