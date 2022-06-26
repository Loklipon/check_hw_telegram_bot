import logging
import os
import requests
import time

from dotenv import load_dotenv
from http import HTTPStatus
from telegram import Bot

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет готовое сообщение."""
    logging.info('Сообщение успешно отправлено')
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Делает API-запрос и возвращает полученный ответ в нужном формате."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    if requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params
    ).status_code == HTTPStatus.OK:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
        return response.json()
    else:
        logging.error('Эндпоинт недоступен')
        raise ValueError


def check_response(response):
    """Проверяет ответ на соответствие требованиям.
    и возвращает необходимый элемент.
    """
    if (
        (type(response['homeworks']) == list)
        and (len(response['homeworks']) != 0)
    ):
        homework = response['homeworks'][0]
        return homework
    else:
        logging.error('Результат не соответствует ожиданиям')
        raise ValueError


def parse_status(homework):
    """Проверяет элемент на соответствие требованиям.
    и формирует необходимый результат.
    """
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        logging.error('Отсутствуют ожидаемые ключи в ответе API')
        raise KeyError
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет наличие необходимых переменных окружения."""
    if (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        return True
    else:
        logging.critical('Отсутствуют обязательные переменные окружения')
        return False


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while check_tokens():
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            logging.debug('Отсутствие в ответе новых статусов')
            return ValueError


if __name__ == '__main__':
    main()
