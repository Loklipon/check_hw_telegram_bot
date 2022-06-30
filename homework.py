import logging
import os
import requests
import time

from dotenv import load_dotenv
from http import HTTPStatus
from telegram import Bot

load_dotenv()


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


def send_message(bot, message) -> None:
    """Отправляет готовое сообщение."""
    try:
        response = bot.send_message(TELEGRAM_CHAT_ID, message)
        if response.message_id:
            logging.info('Сообщение успешно отправлено')
    except Exception:
        raise Exception('Сообщение в бот не было отправлено')


def get_api_answer(current_timestamp) -> dict:
    """Делает API-запрос и возвращает полученный ответ в нужном формате."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        raise Exception(f'Эндпоинт недоступен. URL: {ENDPOINT}.'
                        f'Заголовки: {HEADERS}. Параметры: {params}')
    except Exception:
        raise Exception(f'Эндпоинт недоступен. URL: {ENDPOINT}.'
                        f'Заголовки: {HEADERS}. Параметры: {params}')


def check_response(response) -> dict:
    """Проверяет ответ на соответствие требованиям.
    и возвращает необходимый элемент.
    """
    logging.info('Начали проверять ответ от сервера')
    if (
        isinstance(response, dict)
        and 'homeworks' in response
        and isinstance(response['homeworks'], list)
        and len(response['homeworks']) != 0
    ):
        if len(response['homeworks']) == 0:
            logging.debug('Нет обновлений домашних работ')
        else:
            homework = response['homeworks'][0]
            return homework
    raise TypeError('Результат запроса API не соответствует ожиданиям')


def parse_status(homework):
    """Проверяет элемент на соответствие требованиям.
    и формирует необходимый результат.
    """
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        raise KeyError('Отсутствуют ожидаемые ключи в ответе API')
    homework_status = homework['status']
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    raise KeyError('Отсутствуют ожидаемые ключи в ответе API')


def check_tokens() -> bool:
    """Проверяет наличие необходимых переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        return False


def main() -> None:
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            check_tokens()
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            current_timestamp = int(time.time())
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
    logging.basicConfig(
        format='%(asctime)s, %(levelname)s, %(message)s',
        handlers=logging.StreamHandler
    )
