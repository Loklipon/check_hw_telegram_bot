class NetworkProblem(Exception):
    """Ошибка сети."""

    pass


class SendMessageError(Exception):
    """Ошибка отправки сообщения."""

    pass


class APIError(Exception):
    """Ошибка API."""

    pass
