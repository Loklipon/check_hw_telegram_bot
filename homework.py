import logging
import os
import requests
import time

from dotenv import load_dotenv
from http import HTTPStatus
from telegram import Bot

from exceptions import NetworkProblem, SendMessageError, APIError, TokensError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
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
    except SendMessageError:
        raise SendMessageError('Сообщение в бот не было отправлено')


def get_api_answer(current_timestamp) -> dict:
    """Делает API-запрос и возвращает полученный ответ в нужном формате."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    except NetworkProblem:
        raise NetworkProblem(f'Эндпоинт недоступен. URL: {ENDPOINT}.'
                             f'Заголовки: {HEADERS}. Параметры: {params}')
    else:
        if response.status_code == HTTPStatus.OK:
            return response.json()
        raise NetworkProblem(
            f'API вернул ответ с неподходящим статусом: {response.status_code}'
        )


def check_response(response) -> dict:
    """Проверяет ответ на соответствие требованиям.
    и возвращает необходимый элемент.
    """
    logging.info('Начали проверять ответ от сервера')
    if 'homeworks' not in response:
        raise TypeError('Отсутствует ключ homework в ответе от API яндекса')
    if (
        not isinstance(response, dict)
        or not isinstance(response['homeworks'], list)
    ):
        raise APIError('Неверный тип данных в ответет API')
    if len(response['homeworks']) == 0:
        logging.debug('Нет обновлений домашних работ')
    else:
        homework = response['homeworks'][0]
        return homework


def parse_status(homework):
    """Проверяет элемент на соответствие требованиям.
    и формирует необходимый результат.
    """
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        raise KeyError('Отсутствуют ожидаемые ключи в ответе API')
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    raise APIError('Отсутствуют ожидаемые ключи в ответе API')


def check_tokens() -> bool:
    """Проверяет наличие необходимых переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if check_tokens():
        bot = Bot(token=TELEGRAM_TOKEN)
        current_timestamp = 1657370096
        while True:
            try:
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
    else:
        raise TokensError('Отсутствуют необходимые переменные окружения')


if __name__ == '__main__':
    main()
    logging.basicConfig(
        format='%(asctime)s, %(levelname)s, %(message)s',
        handlers=[logging.StreamHandler]
    )
