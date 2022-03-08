import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import Filters, MessageHandler, Updater

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename=__file__ + '.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s, %(lineno)d',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000,
                              backupCount=5)
logger.addHandler(handler)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HOMEWORK_STATUS = {
    'reviewing': 'Работа взята в ревью',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
    'rejected': 'В работе нашлись ошибки.'
}
API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
TIME_SLEEP = 300


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        if homework_status not in HOMEWORK_STATUS:
            return 'Неизвестный статус!'
        verdict = HOMEWORK_STATUS[homework_status]
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    except Exception as e:
        logging.exception(f'Ошибка parse_homework_status: {e}')


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(API, params=params, headers=HEADERS)
        return response.json()
    except requests.RequestException as e:
        logging.error(e, exc_info=True)


def send_message(message, bot_client):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        logging.exception(f'Сообщение не отправилось! Ошибка {e}')

    def main():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        updater = Updater(bot=bot, use_context=True)
        updater.dispatcher.add_handler(
            MessageHandler(Filters.text, send_message))
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler('main.log', maxBytes=50000000,
                                      backupCount=3)
        logger.addHandler(handler)

        current_timestamp = int(time.time())

        while True:
            try:
                new_homework = get_homework_statuses(current_timestamp)
                if new_homework.get('homeworks'):
                    send_message(
                        parse_homework_status(
                            new_homework.get('homeworks')[0]))
                current_timestamp = new_homework.get('current_date',
                                                     current_timestamp)
                TIME_SLEEP

            except Exception as e:
                print(f'Бот столкнулся с ошибкой: {e}')
                TIME_SLEEP

    if __name__ == '__main__':
        main()
