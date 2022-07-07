class NetworkProblem(Exception):
    """Ошибка сети."""

    pass


class SendMessageError(Exception):
    """Ошибка отправки сообщения."""

    pass


class ErrorFromAPI(Exception):
    """Ошибка API."""

    pass
