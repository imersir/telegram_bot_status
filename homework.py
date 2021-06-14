import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import Filters, MessageHandler, Updater

load_dotenv()

# Глобальная конфигурация для всех логеров
logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log', filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s, %(lineno)d',
)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        if homework_status == 'rejected':
            verdict = 'К сожалению в работе нашлись ошибки.'
        elif homework_status == 'reviewing':
            verdict = 'Работа взята в ревью'
        else:
            verdict = ('Ревьюеру всё понравилось, '
                       'можно приступать к следующему уроку.')
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    except Exception as e:
        logging.exception(f'Ошибка parse_homework_status: {e}')


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(API, params=params, headers=headers)
        return homework_statuses.json()
    except Exception as e:
        logging.error(f'Ошибка get_homework_statuses: {e}')
        send_message(f'Ошибка {e}', bot_client=bot)


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    updater = Updater(bot=bot, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, send_message))
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler('main.log', maxBytes=50000000, backupCount=3)
    logger.addHandler(handler)

    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]))
            # обновить timestamp
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(5)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(300)


if __name__ == '__main__':
    main()
